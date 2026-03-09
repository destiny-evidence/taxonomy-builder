"""Round-trip test: import TTL with restrictions and dual-typing, export, verify."""

from datetime import datetime

import pytest
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SKOS
from sqlalchemy.ext.asyncio import AsyncSession

from taxonomy_builder.models.project import Project
from taxonomy_builder.models.published_version import PublishedVersion
from taxonomy_builder.services.concept_service import ConceptService
from taxonomy_builder.services.project_service import ProjectService
from taxonomy_builder.services.skos_export_service import SKOSExportService
from taxonomy_builder.services.skos_import_service import SKOSImportService
from taxonomy_builder.services.snapshot_service import SnapshotService

ROUND_TRIP_TTL = b"""
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://example.org/> .

ex:CodingAnnotation a owl:Class ;
    rdfs:label "CodingAnnotation" .

ex:ConceptSchemeAnnotation a owl:Class ;
    rdfs:label "Concept Scheme Annotation" .

ex:StringAnnotation a owl:Class ;
    rdfs:subClassOf ex:CodingAnnotation ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty ex:codedValue ;
        owl:allValuesFrom xsd:string
    ] ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty ex:targetScheme ;
        owl:allValuesFrom ex:ConceptSchemeAnnotation
    ] ;
    rdfs:label "String Annotation" .

ex:EducationLevelConcept a owl:Class ;
    rdfs:subClassOf skos:Concept ;
    rdfs:label "Education Level Concept" .

ex:EducationLevelScheme a skos:ConceptScheme ;
    rdfs:label "Education Levels" .

ex:Primary a ex:EducationLevelConcept , skos:Concept ;
    skos:inScheme ex:EducationLevelScheme ;
    skos:prefLabel "Primary" ;
    skos:definition "Primary education level" .

ex:codedValue a rdf:Property ;
    rdfs:label "coded value" ;
    rdfs:domain ex:CodingAnnotation .

ex:targetScheme a rdf:Property ;
    rdfs:label "target scheme" ;
    rdfs:domain ex:CodingAnnotation .
"""


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    project = Project(name="Round Trip Project", namespace="http://example.org/")
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_round_trip_restrictions_and_dual_typing(
    db_session: AsyncSession, project: Project,
):
    """Import → snapshot → export preserves restrictions and concept dual-typing."""
    # 1. Import
    import_service = SKOSImportService(db_session)
    result = await import_service.execute(project.id, ROUND_TRIP_TTL, "test.ttl")
    # CodingAnnotation, ConceptSchemeAnnotation, StringAnnotation, EducationLevelConcept
    assert len(result.classes_created) == 4

    # 2. Build snapshot (expunge identity map so service loads fresh from DB)
    db_session.expunge_all()
    project_service = ProjectService(db_session)
    concept_service = ConceptService(db_session)
    snapshot_service = SnapshotService(db_session, project_service, concept_service)
    snapshot = await snapshot_service.build_snapshot(project.id)

    # 3. Create a PublishedVersion so we can use export_published_version
    pv = PublishedVersion(
        project_id=project.id,
        version="1.0",
        title="v1.0",
        snapshot=snapshot.model_dump(mode="json"),
        published_at=datetime.now(),
    )
    db_session.add(pv)
    await db_session.flush()

    # 4. Export
    export_service = SKOSExportService(db_session)
    turtle_output = await export_service.export_published_version(pv, "turtle")

    g = Graph()
    g.parse(data=turtle_output, format="turtle")

    # --- Verify both restrictions round-tripped ---
    string_ann = URIRef("http://example.org/StringAnnotation")
    subclass_objects = list(g.objects(string_ann, RDFS.subClassOf))
    restriction_bnodes = [n for n in subclass_objects if isinstance(n, BNode)]
    assert len(restriction_bnodes) == 2

    # Collect restriction details: {property_uri: value_uri}
    restrictions = {}
    for bnode in restriction_bnodes:
        assert (bnode, RDF.type, OWL.Restriction) in g
        prop = g.value(bnode, OWL.onProperty)
        value = g.value(bnode, OWL.allValuesFrom)
        restrictions[str(prop)] = str(value)

    # xsd:string restriction (external datatype)
    assert restrictions["http://example.org/codedValue"] == (
        "http://www.w3.org/2001/XMLSchema#string"
    )
    # Custom class restriction (internal reference)
    assert restrictions["http://example.org/targetScheme"] == (
        "http://example.org/ConceptSchemeAnnotation"
    )

    # Named superclass also preserved
    uriref_supers = [n for n in subclass_objects if isinstance(n, URIRef)]
    assert URIRef("http://example.org/CodingAnnotation") in uriref_supers

    # --- Collateral damage check: labels survived ---
    assert (string_ann, RDFS.label, Literal("String Annotation")) in g
    coding_ann = URIRef("http://example.org/CodingAnnotation")
    assert (coding_ann, RDFS.label, Literal("CodingAnnotation")) in g

    # --- Verify concept-typed class was imported ---
    ed_concept_cls = URIRef("http://example.org/EducationLevelConcept")
    assert (ed_concept_cls, RDF.type, OWL.Class) in g

    # Note: skos:Concept as rdfs:subClassOf does NOT round-trip because the
    # ClassSuperclass join table can only reference project-local OntologyClass
    # records. External URIs (skos:Concept, owl:Thing) are lost during import.
    # This is a known limitation — see #109 / WELL_KNOWN_SUPERCLASS_URIS.

    # --- Verify concept dual-typing ---
    # Concept URI is computed as scheme_uri/identifier during import
    primary = URIRef("http://example.org/EducationLevelScheme/Primary")
    types = set(g.objects(primary, RDF.type))
    assert SKOS.Concept in types
    assert ed_concept_cls in types

    # Concept metadata survived
    assert (primary, SKOS.prefLabel, Literal("Primary")) in g
    assert (primary, SKOS.definition, Literal("Primary education level")) in g
