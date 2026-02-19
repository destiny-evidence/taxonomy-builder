import type { ComponentChildren } from "preact";
import { useEffect, useRef } from "preact/hooks";
import "./Modal.css";

interface ModalProps {
  isOpen: boolean;
  title: string;
  children: ComponentChildren;
  onClose: () => void;
}

export function Modal({ isOpen, title, children, onClose }: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen) {
      dialog.showModal();
    } else {
      dialog.close();
    }
  }, [isOpen]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const handleCancel = (e: Event) => {
      e.preventDefault();
      onClose();
    };

    dialog.addEventListener("cancel", handleCancel);
    return () => dialog.removeEventListener("cancel", handleCancel);
  }, [onClose]);

  const handleBackdropClick = (e: MouseEvent) => {
    if (e.target === dialogRef.current) {
      onClose();
    }
  };

  return (
    <dialog ref={dialogRef} class="modal" onClick={handleBackdropClick}>
      <div class="modal__content">
        <header class="modal__header">
          <h2 class="modal__title">{title}</h2>
          <button
            type="button"
            class="modal__close"
            onClick={onClose}
            aria-label="Close"
          >
            &times;
          </button>
        </header>
        <div class="modal__body">{isOpen && children}</div>
      </div>
    </dialog>
  );
}
