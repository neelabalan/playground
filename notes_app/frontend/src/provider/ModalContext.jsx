import React, { createContext, useContext, useEffect, useState } from "react";
// import getScrollBarWidth from "./utils/getScrollBarWidth";

const ModalContext = createContext({});
const useModal = () => useContext(ModalContext);

const ModalProvider = ({ children, ...props }) => {
  const htmlTag = document.querySelector("html");
  const [modalIsOpen, setModalIsOpen] = useState(false);
  const modalAnimationDuration = 400;
  const [content, setContent] = useState({id: '', note: ''});

  // Handle open
  const handleOpen = (event) => {
    event.preventDefault();
    if (htmlTag) {
      setModalIsOpen(true);
      htmlTag.classList.add("modal-is-open", "modal-is-opening");
      setTimeout(() => {
        htmlTag.classList.remove("modal-is-opening");
      }, modalAnimationDuration);
    }
  };

  // Handle close
  const handleClose = (event) => {
    event.preventDefault();
    if (htmlTag) {
      htmlTag.classList.add("modal-is-closing");
      setTimeout(() => {
        setModalIsOpen(false);
        htmlTag.classList.remove("modal-is-open", "modal-is-closing");
      }, modalAnimationDuration);
    }
    setContent({id: '', note: ''})
  };

  // Handle escape key
  useEffect(() => {
    const handleEscape = (event) => {
      if (!modalIsOpen) return;
      if (event.key === "Escape") {
        handleClose(event);
      }
    };
    window.addEventListener("keydown", handleEscape);
    return () => {
      window.removeEventListener("keydown", handleEscape);
    };
  }, [modalIsOpen]);


  return (
    <ModalContext.Provider
      value={{
        modalIsOpen,
        handleOpen,
        handleClose,
        content,
        setContent,
        ...props,
      }}
    >
      {children}
    </ModalContext.Provider>
  );
};

export { ModalProvider, useModal };
