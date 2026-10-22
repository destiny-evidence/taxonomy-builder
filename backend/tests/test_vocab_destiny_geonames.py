"""Tests for the DESTINY GeoNames location import file.

The file is imported into a project that already holds evrepo-core, so these
tests check it imports cleanly on top of the core, and that a geoparse payload
shaped the way the geoparsing robot will emit it expands to the intended triples
via the generated JSON-LD context.
"""

import json
from pathlib import Path

import pytest
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import OWL, RDF, RDFS, XSD
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.project import Project
from taxonomy_builder.services.concept_service import ConceptService
from taxonomy_builder.services.context_generation_service import ContextGenerationService
from taxonomy_builder.services.project_service import ProjectService
from taxonomy_builder.services.skos_import_service import SKOSImportService
from taxonomy_builder.services.snapshot_service import SnapshotService

_VOCAB_ROOT = Path(__file__).resolve().parents[2] / "vocab"
_CORE_TTL = _VOCAB_ROOT / "evrepo-core" / "evrepo-core.ttl"
_GEONAMES_TTL = _VOCAB_ROOT / "destiny" / "geonames-location.ttl"
_STANDALONE_TTL = _VOCAB_ROOT / "destiny" / "geonames-location-standalone.ttl"

EVREPO = Namespace("https://vocab.evidence-repository.org/")
DSNY = Namespace("https://vocab.destiny-evidence.org/")
GN = Namespace("http://www.geonames.org/ontology#")
GEO = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")

NEW_CORE_PROPERTIES = {
    EVREPO.mentionText,
    EVREPO.startChar,
    EVREPO.endChar,
    EVREPO.codingScore,
}


def _core_without_new_properties() -> bytes:
    """The core as deployed projects hold it today, before the span properties."""
    g = Graph(bind_namespaces="none")
    g.parse(_CORE_TTL, format="turtle")
    for prop in NEW_CORE_PROPERTIES:
        g.remove((prop, None, None))
    return g.serialize(format="turtle").encode()


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    project = Project(
        name="DESTINY",
        namespace="https://vocab.destiny-evidence.org/",
        identifier_prefix="DSNY",
    )
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def test_project(db_session: AsyncSession) -> Project:
    """A scratch project, as used for trying the standalone file in staging."""
    project = Project(
        name="GeoNames test",
        namespace="https://vocab.evidence-repository.org/geonames-test",
        identifier_prefix="GNT",
    )
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


def _import_service(db_session: AsyncSession) -> SKOSImportService:
    return SKOSImportService(db_session, project_service=ProjectService(db_session))


async def _import_core_then_geonames(db_session: AsyncSession, project: Project):
    await _import_service(db_session).execute(
        project.id, _core_without_new_properties(), "evrepo-core.ttl"
    )
    return await _import_service(db_session).execute(
        project.id, _GEONAMES_TTL.read_bytes(), "geonames-location.ttl"
    )


def test_core_defines_span_and_score_properties() -> None:
    g = Graph()
    g.parse(_CORE_TTL, format="turtle")
    for prop in NEW_CORE_PROPERTIES:
        assert (prop, RDF.type, OWL.DatatypeProperty) in g
        assert (prop, RDFS.domain, EVREPO.CodingAnnotation) in g


def test_core_terms_in_import_file_match_core() -> None:
    """The import file repeats the new core terms; they must not drift."""
    core = Graph()
    core.parse(_CORE_TTL, format="turtle")
    geonames = Graph()
    geonames.parse(_GEONAMES_TTL, format="turtle")

    repeated = {s for s in geonames.subjects() if str(s).startswith(str(EVREPO))}
    assert repeated == NEW_CORE_PROPERTIES
    for prop in repeated:
        assert set(geonames.predicate_objects(prop)) == set(core.predicate_objects(prop))


@pytest.mark.asyncio
async def test_imports_cleanly_on_top_of_core(
    db_session: AsyncSession, project: Project
) -> None:
    result = await _import_core_then_geonames(db_session, project)

    assert result.warnings == []
    assert [v for v in result.validation_issues if v.severity != "info"] == []
    assert {c.uri for c in result.classes_created} == {
        str(GN.Feature),
        str(GEO.SpatialThing),
        str(GN.GeonamesFeature),
        str(GN.Class),
        str(GN.Code),
        str(DSNY.LocationCodingAnnotation),
    }
    assert {p.identifier for p in result.properties_created} == {
        "mentionText",
        "startChar",
        "endChar",
        "codingScore",
        "countryCode",
        "geonamesID",
        "lat",
        "long",
        "featureClass",
        "featureCode",
        "mentionedPlace",
    }


@pytest.mark.asyncio
async def test_reimport_is_a_no_op(db_session: AsyncSession, project: Project) -> None:
    await _import_core_then_geonames(db_session, project)
    again = await _import_service(db_session).execute(
        project.id, _GEONAMES_TTL.read_bytes(), "geonames-location.ttl"
    )
    assert again.classes_created == []
    assert again.properties_created == []


@pytest.mark.asyncio
async def test_robot_payload_expands_through_generated_context(
    db_session: AsyncSession, project: Project
) -> None:
    await _import_core_then_geonames(db_session, project)
    await _assert_robot_payload_expands(db_session, project)


async def _assert_robot_payload_expands(db_session: AsyncSession, project: Project) -> None:
    db_session.expunge_all()
    snapshot = await SnapshotService(
        db_session,
        project_service=ProjectService(db_session),
        concept_service=ConceptService(db_session),
    ).build_snapshot(project.id)
    context = ContextGenerationService().generate(snapshot)

    india = URIRef("http://sws.geonames.org/1269750/")
    payload = {
        **context,
        "@type": "Investigation",
        "mentionedPlace": [
            {
                "@type": "LocationCodingAnnotation",
                # Compact IRI, not the bare "coded" alias: status is "@type": "@id",
                # so a bare term expands document-relative, not via the context.
                "status": "evrepo:coded",
                "codedBy": "mordecai3/3.0.0",
                "codedValue": {
                    "@id": str(india),
                    "@type": "gn:GeonamesFeature",
                    "countryCode": "IN",
                    "geonamesID": "1269750",
                    "lat": 22.0,
                    "long": 79.0,
                    "featureClass": {"@id": "gn:A"},
                    "featureCode": {"@id": "gn:A.PCLI"},
                },
                "supportingText": "Heat exposure was assessed in rural India.",
                "mentionText": "India",
                "startChar": 35,
                "endChar": 40,
                "codingScore": 0.97,
            }
        ],
    }
    g = Graph()
    g.parse(data=json.dumps(payload), format="json-ld")

    annotation = g.value(predicate=RDF.type, object=DSNY.LocationCodingAnnotation)
    assert annotation is not None
    assert (None, DSNY.mentionedPlace, annotation) in g
    assert (annotation, EVREPO.status, EVREPO.coded) in g
    assert (annotation, EVREPO.codedValue, india) in g
    assert (india, RDF.type, GN.GeonamesFeature) in g
    assert (india, GN.countryCode, Literal("IN", datatype=XSD.string)) in g
    assert (india, GN.geonamesID, Literal("1269750", datatype=XSD.string)) in g
    assert g.value(india, GEO.lat).toPython() == pytest.approx(22.0)
    assert g.value(india, GEO.long).toPython() == pytest.approx(79.0)
    assert (india, GN.featureClass, GN.A) in g
    assert (india, GN.featureCode, URIRef(str(GN) + "A.PCLI")) in g
    assert g.value(annotation, EVREPO.mentionText).toPython() == "India"
    assert g.value(annotation, EVREPO.startChar).toPython() == 35
    assert g.value(annotation, EVREPO.endChar).toPython() == 40
    assert float(g.value(annotation, EVREPO.codingScore).toPython()) == pytest.approx(0.97)


STANDALONE_CORE_SUBSET = {
    EVREPO.Investigation,
    EVREPO.CodingAnnotation,
    EVREPO.CodingStatus,
    EVREPO.coded,
    EVREPO.notApplicable,
    EVREPO.notReported,
    EVREPO.codedValue,
    EVREPO.supportingText,
    EVREPO.codedBy,
    EVREPO.status,
}
# Narrowed to CodingAnnotation in the standalone file, because the core's union
# domain names ObservedResult and EffectEstimate, which the subset leaves out.
NARROWED_DOMAIN = {EVREPO.supportingText, EVREPO.codedBy}


def _named_subjects(g: Graph) -> set[URIRef]:
    return {s for s in g.subjects() if isinstance(s, URIRef)}


def _description_of(g: Graph, subjects: set[URIRef]) -> Graph:
    """Triples about *subjects*, following blank nodes (e.g. OWL restrictions)."""
    out = Graph()
    todo: list = list(subjects)
    seen: set = set()
    while todo:
        node = todo.pop()
        if node in seen:
            continue
        seen.add(node)
        for p, o in g.predicate_objects(node):
            out.add((node, p, o))
            if isinstance(o, BNode):
                todo.append(o)
    return out


def test_standalone_repeats_the_destiny_import_verbatim() -> None:
    standalone = Graph()
    standalone.parse(_STANDALONE_TTL, format="turtle")
    destiny = Graph()
    destiny.parse(_GEONAMES_TTL, format="turtle")

    repeated = _description_of(standalone, _named_subjects(destiny))
    assert isomorphic(repeated, destiny)


def test_standalone_core_subset_matches_core() -> None:
    standalone = Graph()
    standalone.parse(_STANDALONE_TTL, format="turtle")
    core = Graph()
    core.parse(_CORE_TTL, format="turtle")

    core_terms = {s for s in _named_subjects(standalone) if str(s).startswith(str(EVREPO))}
    assert core_terms == STANDALONE_CORE_SUBSET | NEW_CORE_PROPERTIES

    for term in STANDALONE_CORE_SUBSET - NARROWED_DOMAIN - {EVREPO.CodingStatus}:
        assert set(standalone.predicate_objects(term)) == set(core.predicate_objects(term)), term
    for term in NARROWED_DOMAIN:
        assert (term, RDFS.domain, EVREPO.CodingAnnotation) in standalone
        assert {
            (p, o) for p, o in standalone.predicate_objects(term) if p != RDFS.domain
        } == {(p, o) for p, o in core.predicate_objects(term) if p != RDFS.domain}


@pytest.mark.asyncio
async def test_standalone_imports_cleanly_into_empty_project(
    db_session: AsyncSession, test_project: Project
) -> None:
    result = await _import_service(db_session).execute(
        test_project.id, _STANDALONE_TTL.read_bytes(), "geonames-location-standalone.ttl"
    )

    assert result.warnings == []
    assert [v for v in result.validation_issues if v.severity != "info"] == []
    assert {c.uri for c in result.classes_created} == {
        str(EVREPO.Investigation),
        str(EVREPO.CodingAnnotation),
        str(EVREPO.CodingStatus),
        str(GN.Feature),
        str(GEO.SpatialThing),
        str(GN.GeonamesFeature),
        str(GN.Class),
        str(GN.Code),
        str(DSNY.LocationCodingAnnotation),
    }
    assert {p.identifier for p in result.properties_created} == {
        "codedValue",
        "supportingText",
        "codedBy",
        "status",
        "mentionText",
        "startChar",
        "endChar",
        "codingScore",
        "countryCode",
        "geonamesID",
        "lat",
        "long",
        "featureClass",
        "featureCode",
        "mentionedPlace",
    }


@pytest.mark.asyncio
async def test_robot_payload_expands_in_standalone_project(
    db_session: AsyncSession, test_project: Project
) -> None:
    await _import_service(db_session).execute(
        test_project.id, _STANDALONE_TTL.read_bytes(), "geonames-location-standalone.ttl"
    )
    await _assert_robot_payload_expands(db_session, test_project)


def test_geonames_feature_restates_geonames_wording() -> None:
    for path in (_GEONAMES_TTL, _STANDALONE_TTL):
        g = Graph()
        g.parse(path, format="turtle")
        assert (GN.GeonamesFeature, RDFS.label, Literal("Geonames Feature", lang="en")) in g
        assert (
            GN.GeonamesFeature,
            RDFS.comment,
            Literal(
                "A feature described in geonames database, uniquely defined by its "
                "geonames identifier",
                lang="en",
            ),
        ) in g
