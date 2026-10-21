const form = document.querySelector("#post-form");
const postsContainer = document.querySelector("#posts");
const message = document.querySelector("#message");
const submitButton = document.querySelector("#submit-button");
const reloadButton = document.querySelector("#reload-button");
const titleInput = document.querySelector("#title");
const contentInput = document.querySelector("#content");

async function loadPosts() {
  message.textContent = "Загружаем посты…";

  try {
    const response = await fetch("/posts?limit=20");
    if (!response.ok) throw new Error(`Ошибка сервера: ${response.status}`);

    const posts = await response.json();
    postsContainer.replaceChildren();

    if (posts.length === 0) {
      message.textContent = "Постов пока нет. Создай первый!";
      return true;
    }

    for (const post of posts) {
      const card = document.createElement("article");
      card.className = "post";

      const title = document.createElement("h3");
      title.textContent = post.title;

      const content = document.createElement("p");
      content.textContent = post.content;

      const date = document.createElement("time");
      date.dateTime = post.created_at;
      date.textContent = new Date(post.created_at).toLocaleString("ru-RU");

      card.append(title, content, date);
      postsContainer.append(card);
    }

    message.textContent = "";
    return true;
  } catch (error) {
    message.textContent = `Не удалось загрузить посты: ${error.message}`;
    return false;
  }
}

async function createPost(event) {
  event.preventDefault();
  submitButton.disabled = true;
  message.textContent = "Публикуем пост…";

  const title = titleInput.value.trim();
  const content = contentInput.value.trim();

  if (!title || !content) {
    message.textContent = "Заполни заголовок и текст поста.";
    submitButton.disabled = false;
    return;
  }

  try {
    const response = await fetch("/posts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content }),
    });
    if (!response.ok) throw new Error(`Ошибка сервера: ${response.status}`);

    form.reset();
    if (await loadPosts()) message.textContent = "Пост опубликован.";
  } catch (error) {
    message.textContent = `Не удалось создать пост: ${error.message}`;
  } finally {
    submitButton.disabled = false;
  }
}

form.addEventListener("submit", createPost);
reloadButton.addEventListener("click", loadPosts);
loadPosts();
