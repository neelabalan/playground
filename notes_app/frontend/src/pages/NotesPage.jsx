import { useState, useEffect } from "react";
import ThoughtList from "../components/ThoughtList";
import Modal from "../components/ModalTextInput";
import { ModalProvider } from "../provider/ModalContext";
import ModalButton from "../components/ModalButton";
import SearchBar from "../components/SearchBar";
import useFetchPrivate from "../hooks/useFetchPrivate";

function NotesPage() {
  const [notes, setNotes] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const fetchPrivate = useFetchPrivate();

  useEffect(() => {
    fetchNotes();
  }, []);

  const fetchNotes = async () => {
    const result = await fetchPrivate({
      method: "GET",
      endpoint: "/list_notes?page=1&page_size=50",
    });
    if (result.status === 200 && result.data?.notes) {
      setNotes(
        result.data.notes.map((n) => ({
          id: n.id,
          note: n.note,
          tags: n.tags,
          created_at: n.created_at,
          updated_at: n.updated_at,
        }))
      );
    }
  };

  const addNote = async (content) => {
    if (content.id) {
      const result = await fetchPrivate({
        method: "PUT",
        endpoint: `/note/${content.id}`,
        body: { note: content.note },
      });
      if (result.status === 200) {
        setNotes(
          notes.map((item) =>
            item.id === content.id ? { ...item, note: content.note } : item
          )
        );
      }
    } else {
      const result = await fetchPrivate({
        method: "POST",
        endpoint: "/create_note",
        body: { note: content.note },
      });
      if (result.status === 201) {
        fetchNotes();
      }
    }
  };

  const handleDelete = async (id) => {
    const result = await fetchPrivate({
      method: "DELETE",
      endpoint: `/note/${id}`,
    });
    if (result.status === 200) {
      setNotes(notes.filter((n) => n.id !== id));
    }
  };

  return (
    <div>
      <ModalProvider>
        <div className="wrapper">
          <div className="container">
            <SearchBar setSearchTerm={setSearchTerm}></SearchBar>
            <ModalButton>Add</ModalButton>
          </div>
        </div>
        <Modal addThought={addNote} />
        <ThoughtList
          thoughts={notes}
          searchTerm={searchTerm}
          handleDelete={handleDelete}
        />
      </ModalProvider>
    </div>
  );
}

export default NotesPage;
