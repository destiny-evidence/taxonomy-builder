"""Tests for the DESTINY GeoNames location import file.

The file is imported into a project that already holds evrepo-core, so these
tests check it imports cleanly on top of the core, and that a geoparse payload
shaped the way the geoparsing robot will emit it expands to the intended triples
via the generated JSON-LD context.
"""

import json
from pathlib import Path

import pytest
from rdflib import Graph, Literal, Namespace, URIRef
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

EVREPO = Namespace("https://vocab.evidence-repository.org/")
DSNY = Namespace("https://vocab.destiny-evidence.org/")
GN = Namespace("http://www.geonames.org/ontology#")

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
    assert (india, GN.featureClass, GN.A) in g
    assert (india, GN.featureCode, URIRef(str(GN) + "A.PCLI")) in g
    assert g.value(annotation, EVREPO.mentionText).toPython() == "India"
    assert g.value(annotation, EVREPO.startChar).toPython() == 35
    assert g.value(annotation, EVREPO.endChar).toPython() == 40
    assert float(g.value(annotation, EVREPO.codingScore).toPython()) == pytest.approx(0.97)
