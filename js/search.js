function searchBlog() {
    var searchInput = document.getElementById("searchInput").value.toLowerCase();
    var blogPostTitles = document.querySelectorAll(".portfolio-title");

    var searchResults = document.getElementById("searchResults");
    searchResults.innerHTML = ""; // Clear previous results

    blogPostTitles.forEach(function(title) {
        var postTitle = title.textContent.toLowerCase();
        if (postTitle.includes(searchInput)) {
            var clonedPost = title.closest('.card').cloneNode(true);
            searchResults.appendChild(clonedPost); // Clone and display matching posts
        }
    });
}
