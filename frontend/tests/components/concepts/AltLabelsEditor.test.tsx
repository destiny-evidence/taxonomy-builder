import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/preact";
import { AltLabelsEditor } from "../../../src/components/concepts/AltLabelsEditor";

describe("AltLabelsEditor", () => {
  const defaultProps = {
    labels: [],
    onChange: vi.fn(),
  };

  describe("display", () => {
    it("shows empty message when no alt labels", () => {
      render(<AltLabelsEditor {...defaultProps} />);

      expect(screen.getByText(/No alternative labels/)).toBeInTheDocument();
    });

    it("displays existing labels as chips", () => {
      render(
        <AltLabelsEditor
          {...defaultProps}
          labels={["Label One", "Label Two"]}
        />
      );

      expect(screen.getByText("Label One")).toBeInTheDocument();
      expect(screen.getByText("Label Two")).toBeInTheDocument();
    });

    it("shows remove button for each label", () => {
      render(
        <AltLabelsEditor
          {...defaultProps}
          labels={["Label One", "Label Two"]}
        />
      );

      const removeButtons = screen.getAllByTitle("Remove alternative label");
      expect(removeButtons).toHaveLength(2);
    });
  });

  describe("adding labels", () => {
    it("shows input field for adding new labels", () => {
      render(<AltLabelsEditor {...defaultProps} />);

      expect(screen.getByPlaceholderText(/Add alternative label/)).toBeInTheDocument();
    });

    it("calls onChange with new label when Enter pressed", () => {
      const onChange = vi.fn();
      render(<AltLabelsEditor labels={[]} onChange={onChange} />);

      const input = screen.getByPlaceholderText(/Add alternative label/);
      fireEvent.input(input, { target: { value: "New Label" } });
      fireEvent.keyDown(input, { key: "Enter" });

      expect(onChange).toHaveBeenCalledWith(["New Label"]);
    });

    it("calls onChange with new label when Add button clicked", () => {
      const onChange = vi.fn();
      render(<AltLabelsEditor labels={[]} onChange={onChange} />);

      const input = screen.getByPlaceholderText(/Add alternative label/);
      fireEvent.input(input, { target: { value: "New Label" } });
      fireEvent.click(screen.getByText("Add"));

      expect(onChange).toHaveBeenCalledWith(["New Label"]);
    });

    it("appends to existing labels", () => {
      const onChange = vi.fn();
      render(
        <AltLabelsEditor
          labels={["Existing"]}
          onChange={onChange}
        />
      );

      const input = screen.getByPlaceholderText(/Add alternative label/);
      fireEvent.input(input, { target: { value: "New Label" } });
      fireEvent.keyDown(input, { key: "Enter" });

      expect(onChange).toHaveBeenCalledWith(["Existing", "New Label"]);
    });

    it("does not add empty labels", () => {
      const onChange = vi.fn();
      render(<AltLabelsEditor labels={[]} onChange={onChange} />);

      const input = screen.getByPlaceholderText(/Add alternative label/);
      fireEvent.input(input, { target: { value: "   " } });
      fireEvent.keyDown(input, { key: "Enter" });

      expect(onChange).not.toHaveBeenCalled();
    });

    it("does not add duplicate labels (case-insensitive)", () => {
      const onChange = vi.fn();
      render(
        <AltLabelsEditor
          labels={["Existing"]}
          onChange={onChange}
        />
      );

      const input = screen.getByPlaceholderText(/Add alternative label/);
      fireEvent.input(input, { target: { value: "EXISTING" } });
      fireEvent.keyDown(input, { key: "Enter" });

      expect(onChange).not.toHaveBeenCalled();
    });

    it("clears input after adding label", () => {
      const onChange = vi.fn();
      render(<AltLabelsEditor labels={[]} onChange={onChange} />);

      const input = screen.getByPlaceholderText(/Add alternative label/) as HTMLInputElement;
      fireEvent.input(input, { target: { value: "New Label" } });
      fireEvent.keyDown(input, { key: "Enter" });

      expect(input.value).toBe("");
    });

    it("trims whitespace from labels", () => {
      const onChange = vi.fn();
      render(<AltLabelsEditor labels={[]} onChange={onChange} />);

      const input = screen.getByPlaceholderText(/Add alternative label/);
      fireEvent.input(input, { target: { value: "  Trimmed Label  " } });
      fireEvent.keyDown(input, { key: "Enter" });

      expect(onChange).toHaveBeenCalledWith(["Trimmed Label"]);
    });

    it("disables Add button when input is empty", () => {
      render(<AltLabelsEditor {...defaultProps} />);

      const addButton = screen.getByText("Add");
      expect(addButton).toBeDisabled();
    });
  });

  describe("removing labels", () => {
    it("calls onChange with filtered list when remove clicked", () => {
      const onChange = vi.fn();
      render(
        <AltLabelsEditor
          labels={["Label One", "Label Two", "Label Three"]}
          onChange={onChange}
        />
      );

      const removeButtons = screen.getAllByTitle("Remove alternative label");
      fireEvent.click(removeButtons[1]); // Remove "Label Two"

      expect(onChange).toHaveBeenCalledWith(["Label One", "Label Three"]);
    });
  });

  describe("read-only mode", () => {
    it("hides input field in read-only mode", () => {
      render(
        <AltLabelsEditor
          {...defaultProps}
          labels={["Label"]}
          readOnly
        />
      );

      expect(screen.queryByPlaceholderText(/Add alternative label/)).not.toBeInTheDocument();
    });

    it("hides remove buttons in read-only mode", () => {
      render(
        <AltLabelsEditor
          {...defaultProps}
          labels={["Label One", "Label Two"]}
          readOnly
        />
      );

      expect(screen.queryByTitle("Remove alternative label")).not.toBeInTheDocument();
    });

    it("still displays labels in read-only mode", () => {
      render(
        <AltLabelsEditor
          {...defaultProps}
          labels={["Label One"]}
          readOnly
        />
      );

      expect(screen.getByText("Label One")).toBeInTheDocument();
    });

    it("shows empty message in read-only mode when no labels", () => {
      render(
        <AltLabelsEditor
          {...defaultProps}
          readOnly
        />
      );

      expect(screen.getByText(/No alternative labels/)).toBeInTheDocument();
    });
  });
});
