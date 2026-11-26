import { useEffect, useState } from "react";
import { FiLogOut, FiMenu, FiUser, FiX } from "react-icons/fi";
import { LuGraduationCap } from "react-icons/lu";
import { useAuth } from "../lib/auth.jsx";
import { Link, useLocation } from "../lib/router.jsx";

export function Logo() {
  return (
    <Link to="/" className="logo">
      <span className="logo-mark"><LuGraduationCap aria-hidden="true" /></span>
      LearnSphere
    </Link>
  );
}

const LINKS = {
  student: [["/dashboard", "My learning"]],
  instructor: [["/instructor", "Instructor studio"]],
  admin: [["/admin", "Admin dashboard"]],
};

export function Navbar() {
  const { user, signOut } = useAuth();
  const { path, search } = useLocation();
  const [open, setOpen] = useState(false);
  useEffect(() => setOpen(false), [path, search]);

  const links = [["/", "Home"], ["/courses", "Courses"], ...(LINKS[user?.role] || []),
    ["/verify", "Verify certificate"]];

  return (
    <header className="navbar">
      <div className="container nav-inner">
        <Logo />
        <button type="button" className="icon-btn nav-toggle" aria-expanded={open}
          aria-controls="nav-menu" aria-label={open ? "Close menu" : "Open menu"}
          onClick={() => setOpen(!open)}>
          {open ? <FiX /> : <FiMenu />}
        </button>
        <div id="nav-menu" className={`nav-menu ${open ? "open" : ""}`}>
          <nav aria-label="Main">
            {links.map(([to, label]) => (
              <Link key={to} to={to} aria-current={path === to ? "page" : undefined}>{label}</Link>
            ))}
          </nav>
          <div className="nav-user">
            {user ? (
              <>
                <Link to="/profile" className="user-chip" title="My profile">
                  <FiUser aria-hidden="true" /> <span>{user.name.split(" ")[0]}</span>
                </Link>
                <button type="button" className="btn btn-outline btn-sm" onClick={signOut}>
                  <FiLogOut aria-hidden="true" /> Log out
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn btn-outline btn-sm">Log in</Link>
                <Link to="/register" className="btn btn-primary btn-sm">Sign up</Link>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

export function Footer() {
  const { user } = useAuth();
  return (
    <footer className="footer">
      <div className="container footer-grid">
        <div>
          <Logo />
          <p>Learn at your own pace with video lessons, study materials, quizzes and certificates.</p>
        </div>
        <nav aria-label="Explore">
          <h4>Explore</h4>
          <Link to="/courses">All courses</Link>
          <Link to="/courses?sort=popular">Popular courses</Link>
          <Link to="/verify">Verify a certificate</Link>
        </nav>
        <nav aria-label="Account">
          <h4>Account</h4>
          {user ? <Link to="/profile">My profile</Link> : (
            <>
              <Link to="/login">Log in</Link>
              <Link to="/register">Create a student account</Link>
              <Link to="/register?role=instructor">Teach on LearnSphere</Link>
            </>
          )}
        </nav>
      </div>
      <div className="container footer-note">
        © {new Date().getFullYear()} LearnSphere. A full stack learning platform project.
      </div>
    </footer>
  );
}
