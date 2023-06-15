// An example array of blog posts (replace with your actual data)
const blogPosts = [
    {
        image: 'path/to/image1.jpg',
        title: 'Blog Post 1',
        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
        link: 'https://aslan04739.github.io/aslanesamai/news-detail.html'
    },
    {
        image: 'path/to/image2.jpg',
        title: 'Blog Post 2',
        description: 'Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.',
        link: 'path/to/blogpost2.html'
    },
    // Add more blog posts as needed
];

// Function to generate the blog post HTML
function generateBlogPost(post) {
    const blogPost = document.createElement('div');
    blogPost.classList.add('blog-post');

    const image = document.createElement('img');
    image.src = post.image;
    blogPost.appendChild(image);

    const title = document.createElement('h2');
    title.textContent = post.title;
    blogPost.appendChild(title);

    const description = document.createElement('p');
    description.textContent = post.description;
    blogPost.appendChild(description);

    const link = document.createElement('a');
    link.href = post.link;
    link.textContent = 'Read More';
    blogPost.appendChild(link);

    return blogPost;
}

// Function to load the blog posts into the blog container
function loadBlogPosts() {
    const blogContainer = document.getElementById('blog-container');
    blogPosts.forEach((post) => {
        const blogPost = generateBlogPost(post);
        blogContainer.appendChild(blogPost);
    });
}

// Call the function to load the blog posts when the page is ready
document.addEventListener('DOMContentLoaded', loadBlogPosts);
