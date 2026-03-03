import React from "react";
import { useModal } from "../provider/ModalContext";

export default function ModalButton({ children, ...props }) {
  const { handleOpen } = useModal();

  return (
    <button className="modal-button" onClick={handleOpen} {...props}>
      {children}
    </button>
  );
}
