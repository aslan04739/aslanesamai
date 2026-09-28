// aslanesamai.com — small progressive enhancements (the site works without JS)
document.documentElement.classList.add("js");
document.addEventListener("DOMContentLoaded", () => {
  const header = document.querySelector(".site-header");
  const onScroll = () => header && header.classList.toggle("scrolled", window.scrollY > 8);
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  // Remember the language the visitor picks (used by the chooser at /)
  document.querySelectorAll("[data-lang]").forEach((a) => a.addEventListener("click", () => { try { localStorage.setItem("lang", a.dataset.lang); } catch (e) {} }));

  // Close the mobile menu after picking a link
  document.querySelectorAll(".menu nav a").forEach((a) => a.addEventListener("click", () => a.closest("details").removeAttribute("open")));

  // Fade sections in as they scroll into view
  const items = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => entries.forEach((en) => {
      if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
    }), { rootMargin: "0px 0px -8% 0px" });
    items.forEach((el) => io.observe(el));
  } else items.forEach((el) => el.classList.add("in"));

  // Load the Calendly widget only when the contact section gets close
  const cal = document.querySelector(".calendly-inline-widget[data-lazy]");
  if (cal && "IntersectionObserver" in window) {
    const load = () => {
      if (window.__calendly) return;
      window.__calendly = true;
      cal.innerHTML = "";
      const s = document.createElement("script");
      s.src = "https://assets.calendly.com/assets/external/widget.js";
      s.async = true;
      document.head.appendChild(s);
    };
    const io = new IntersectionObserver((entries) => { if (entries.some((en) => en.isIntersecting)) { load(); io.disconnect(); } }, { rootMargin: "600px 0px" });
    io.observe(cal);
  }
});
