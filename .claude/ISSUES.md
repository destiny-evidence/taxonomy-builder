# Issues to work through

## 1. Modals are not centred

All modals (create, edit, confirm dialogs) should be both vertically and horizontally centred on the screen.

## 2. Clicking "Edit" does not show the edit modal (Projects & Schemes)

**Affected:** Projects and Schemes (Concepts have a separate issue #5)

**Steps to reproduce:**
- Click on "Edit" on a project or scheme

**Expected:** The edit modal is shown with the entity's current data pre-populated.

**Actual:** Navigation occurs instead of showing the modal (for projects, the project detail page is shown).

## 3. Concept URLs require too much input

Concept URLs require repetitive input of the URL base. The URL should be computed from the scheme's URI plus an identifier.

**Solution:**
- Add an editable `identifier` field to concepts
- Compute the full URL as `{scheme.uri}/{identifier}` (read-only derived field)
- If the scheme has no URI set, use a placeholder base URL (e.g., `http://example.org/concepts/`)

## 4. Concept modal is not reset on successful creation

**Steps to reproduce:**
1. Submit a new concept which is successfully created
2. Click "Add Concept" to create another concept

**Expected:** The "New Concept" modal displays empty.

**Actual:** The "New Concept" modal displays with the previously submitted data still present.

**Note:** Check if this also affects Project and Scheme creation modals.

## 5. Edit Concept modal is empty

**Steps to reproduce:**
1. Click on a concept in a concept scheme
2. Click "Edit" in the sidebar

**Expected:** Edit Concept modal is populated with the selected concept's details.

**Actual:** Edit Concept modal is empty.

**Note:** This is related to but distinct from issue #2 - the edit modal does open for concepts, but it's not populated with data.

## 6. Adding a broader relationship does not update the UI

**Steps to reproduce:**
1. Add a broader relationship to a concept

**Expected:**
- The tree view updates to reflect the new hierarchy
- The concept detail sidebar refreshes to show the updated "Broader" list

**Actual:** The UI does not update. A page refresh is required to display the change.

**Note:** The tree auto-expand already works; the issue is that neither the tree nor the sidebar refreshes after the API call succeeds.
