document.addEventListener('DOMContentLoaded', () => {
    const markdownSource = document.getElementById('markdown-source').value;
    const htmlContent = marked.parse(markdownSource);
    document.getElementById('content').innerHTML = htmlContent;
});
