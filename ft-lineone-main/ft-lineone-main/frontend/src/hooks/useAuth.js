import { useSelector, useDispatch } from "react-redux";
import { loginUser, registerUser, logout } from "../store/userSlice";

function useAuth() {
  const dispatch = useDispatch();
  const { user, isAuthenticated, loading, error } = useSelector((state) => state.user);

  const login = (email, password) => dispatch(loginUser({ email, password }));
  const register = (data) => dispatch(registerUser(data));
  const signOut = () => dispatch(logout());

  return { user, isAuthenticated, loading, error, login, register, logout: signOut };
}

export default useAuth;
