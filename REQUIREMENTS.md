# Taxonomy Builder

This application will be an interface for building taxonomies to support evidence repositories.

It will be built using Python 3.14 and vanilla Typescript for the front-end. It will prefer tools like uv and FastAPI. It will have a comprehensive test suite using pytest and whatever testing framework makes sense for the front-end.

## Requirements

### Taxonomies

A taxonomy is built up of multiple skos ConceptSchemes, but the taxonomy will include a URI prefix which will be used for identifiers for the skos Concepts and Concept schemes.

Example Concept Schemes could be "Intervention", "Climate Impact", "Context", "Health Outcome". Each of these schemes would have multiple levels of Concepts within them.

### Interface

The interface should make it easy to visualise the taxonomy while building it, and reveal lexically and semantically similar concepts.

The hierarchy should be clear to see visually, but without being visually overwhelming.
