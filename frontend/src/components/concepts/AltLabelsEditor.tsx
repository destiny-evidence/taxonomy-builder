import { useState } from "preact/hooks";
import { Button } from "../common/Button";
import "./AltLabelsEditor.css";

interface AltLabelsEditorProps {
  labels: string[];
  onChange: (labels: string[]) => void;
  readOnly?: boolean;
}

export function AltLabelsEditor({
  labels,
  onChange,
  readOnly = false,
}: AltLabelsEditorProps) {
  const [inputValue, setInputValue] = useState("");

  function handleAdd() {
    const trimmed = inputValue.trim();
    if (!trimmed) return;

    // Check for case-insensitive duplicate
    const isDuplicate = labels.some(
      (label) => label.toLowerCase() === trimmed.toLowerCase()
    );
    if (isDuplicate) return;

    onChange([...labels, trimmed]);
    setInputValue("");
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAdd();
    }
  }

  function handleRemove(index: number) {
    onChange(labels.filter((_, i) => i !== index));
  }

  const canAdd = inputValue.trim().length > 0;

  return (
    <div class="alt-labels-editor">
      {labels.length > 0 ? (
        <ul class="alt-labels-editor__list">
          {labels.map((label, index) => (
            <li key={index} class="alt-labels-editor__chip">
              <span class="alt-labels-editor__label">{label}</span>
              {!readOnly && (
                <button
                  class="alt-labels-editor__remove"
                  onClick={() => handleRemove(index)}
                  title="Remove alternative label"
                  type="button"
                >
                  &times;
                </button>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p class="alt-labels-editor__empty">No alternative labels</p>
      )}

      {!readOnly && (
        <div class="alt-labels-editor__add-form">
          <input
            type="text"
            class="alt-labels-editor__input"
            value={inputValue}
            onInput={(e) => setInputValue(e.currentTarget.value)}
            onKeyDown={handleKeyDown}
            placeholder="Add alternative label..."
          />
          <Button size="sm" onClick={handleAdd} disabled={!canAdd}>
            Add
          </Button>
        </div>
      )}
    </div>
  );
}
