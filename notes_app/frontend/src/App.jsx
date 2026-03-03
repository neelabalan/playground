import Route from "./components/Route";
import SignIn from "./pages/SignInPage";
import SignUp from "./pages/SignUpPage";
import useAuth from "./hooks/useAuth";

import "./App.css";
import NotesPage from "./pages/NotesPage";
import HomePage from "./pages/HomePage";
import useNavigation from "./hooks/useNavigation";

function App() {
  const { auth } = useAuth();
  const { currentPath, navigate } = useNavigation();

  const isAuthenticated = !!auth?.accessToken;

  if (currentPath === "/notes" && !isAuthenticated) {
    navigate("/signin");
    return null;
  }

  return (
    <div>
      <div>
        <Route path="/">
          <HomePage />
        </Route>
        <Route path="/signin">
          <SignIn />
        </Route>
        <Route path="/signup">
          <SignUp />
        </Route>
        <Route path="/notes">
          <NotesPage />
        </Route>
      </div>
    </div>
  );
}

export default App;
