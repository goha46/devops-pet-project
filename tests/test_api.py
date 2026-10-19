import pytest


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_post_method(client):
    """
    Создание поста. client.post("/posts",
    json={"title": "...", "content": "..."}).
    Ждём статус 201, а в response.json() проверьте title
    и наличие id и created_at.
    """

    respons_post = client.post("/posts", json={"title": "Test", "content": "Testing..."})
    assert respons_post.status_code == 201

    data = respons_post.json()
    assert data["title"] == "Test"
    assert data["content"] == "Testing..."
    assert "id" in data
    assert "created_at" in data


def test_create_posts(client):
    """
    Список и порядок. Создайте два поста подряд
    (два вызова post), затем client.get("/posts").
    В списке два элемента, и первым идёт тот,
    что создан вторым (новые сверху)
    """

    first_post = {"title": "First test", "content": "First testing..."}
    second_post = {"title": "Second test", "content": "Second testing..."}
    client.post("/posts", json=first_post)
    client.post("/posts", json=second_post)

    respons = client.get("/posts")
    assert respons.status_code == 200

    posts = respons.json()
    assert len(posts) == 2
    assert posts[0]["title"] == second_post["title"]
    assert posts[0]["content"] == second_post["content"]
    assert posts[1]["title"] == first_post["title"]
    assert posts[1]["content"] == first_post["content"]


def test_post_limit(client):
    """
    limit. Создайте три поста, запросите client.get
    ("/posts?limit=2"), проверьте, что пришло два.
    """
    for title in ["First", "Second", "Third"]:
        client.post("/posts", json={"title": title, "content": "Testing..."})

    respons = client.get("/posts?limit=2")
    assert respons.status_code == 200

    posts = respons.json()
    assert len(posts) == 2
    assert [p["title"] for p in posts] == ["Third", "Second"]


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "", "content": "..."},
        {"title": "", "content": ""},
        {"title": "1", "content": ""},
        {"title": "2"},
        {"content": "testing"},
        {"title": "a" * 256, "content": "x"},
    ],
)
def test_post_validation(client, payload):
    """
    Отправьте POST /posts с пустым title, то есть json={"title":
      "", "content": "text"}. Ожидаем статус 422.
    """
    response = client.post("/posts", json=payload)
    assert response.status_code == 422
