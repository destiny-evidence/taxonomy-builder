import type { JSX } from "preact";
import "./Input.css";

interface InputProps {
  label: string;
  name: string;
  type?: "text" | "email" | "url";
  value: string;
  placeholder?: string;
  required?: boolean;
  multiline?: boolean;
  rows?: number;
  error?: string;
  onChange: (value: string) => void;
}

export function Input({
  label,
  name,
  type = "text",
  value,
  placeholder,
  required = false,
  multiline = false,
  rows = 3,
  error,
  onChange,
}: InputProps) {
  const handleChange = (
    e: JSX.TargetedEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    onChange(e.currentTarget.value);
  };

  const inputId = `input-${name}`;

  return (
    <div class={`input-field ${error ? "input-field--error" : ""}`}>
      <label class="input-field__label" for={inputId}>
        {label}
        {required && <span class="input-field__required">*</span>}
      </label>
      {multiline ? (
        <textarea
          id={inputId}
          name={name}
          class="input-field__input input-field__textarea"
          value={value}
          placeholder={placeholder}
          required={required}
          rows={rows}
          onInput={handleChange}
        />
      ) : (
        <input
          id={inputId}
          name={name}
          type={type}
          class="input-field__input"
          value={value}
          placeholder={placeholder}
          required={required}
          onInput={handleChange}
        />
      )}
      {error && <span class="input-field__error">{error}</span>}
    </div>
  );
}
