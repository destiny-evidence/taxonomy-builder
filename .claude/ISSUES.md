# Issues to work through

## Creation modal is not centred

The modal for creating a project, concept scheme, or concept is not centred on the screen. It should be both vertically and horizontally centred.

## Clicking "edit" on a project does not show the edit modal

Action: Click on "edit" on a project

Expected result: The edit modal is shown and I can update the name and description of the project.

Actual result: The project is shown (including concept schemes)

## Concept URLs require too much input

Concept URLs require repetitive input of the URL base. The URL base should be derived from the URL of the concept scheme with the identifier of the concept appended.

## Concept modal is not reset on successful creation

Steps:

- Submit a new concept which is successfully created
- Click "Add Concept" to create another concept

Expected result: The "New Concept" modal displays, empty

Actual result: The "New Concept" modal displays with the previously submitted data still present.

## The Edit concept is empty

Steps:

- Click on a concept in a concept scheme
- Click "Edit" in the sidebar

Expected result:
Edit Concept modal is populated with the selected concept's details.

Actual result: Edit concept modal is empty

## Adding a broader relationship to a concept does not update the UI

Steps:

- Add a broader relationship to a concept

Expected result: UI is updated to reflect the newly added relationship

Actual result: The UI does not update. A page refresh is required to display the change.
