import { useRef, useEffect } from "preact/hooks";
import "./ConfirmDialog.css";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Delete",
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  return (
    <dialog ref={ref} class="confirm-dialog" onClose={onCancel}>
      <div class="confirm-dialog__title">{title}</div>
      <div class="confirm-dialog__message">{message}</div>
      <div class="confirm-dialog__actions">
        <button class="confirm-dialog__btn" onClick={onCancel}>
          Cancel
        </button>
        <button
          class="confirm-dialog__btn confirm-dialog__btn--danger"
          onClick={onConfirm}
        >
          {confirmLabel}
        </button>
      </div>
    </dialog>
  );
}
