console.log("content.js loaded");

function showSections() {
  const sections = document.querySelectorAll('.mobile-rib-section, .desktop-distinct-section');
  sections.forEach(section => {
    section.style.display = 'block';
  });
  if (sections.length > 0) {
    console.log(`Applied display:block to ${sections.length} section(s)`);
  }
}

// Check
showSections();

// Dynamic changes
const observer = new MutationObserver(() => {
  showSections();
});

observer.observe(document.body, {
  childList: true,
  subtree: true
});
