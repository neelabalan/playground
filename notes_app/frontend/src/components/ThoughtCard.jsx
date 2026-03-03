import { FiEdit } from "react-icons/fi";
import { FiTrash2 } from "react-icons/fi";
import { useModal } from "../provider/ModalContext";
import Markdown from 'react-markdown'


export default function ThoughtCard({ thought, handleDelete }) {
  const { handleOpen, setContent } = useModal();
  const editCard = (event) => {
    handleOpen(event)
    console.log(thought)
    setContent(thought)
  }

  return (
    <fieldset role="group">
      <article
        type="text"
        className="thought-card"
        name="text"
        style={{ whiteSpace: "pre-wrap" }}
      >
        <Markdown>{thought.note}</Markdown>
        <div className="icon-container">
          <FiEdit className="edit-icon" onClick={editCard}/>
          <FiTrash2 className="trash-icon" onClick={() => handleDelete(thought.id)}/>
        </div>
      </article>
    </fieldset>
  );
}
