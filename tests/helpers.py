"""여러 테스트 파일에서 함께 쓰는 도우미 함수"""

def create_book(client, headers: dict, author_id: int, **fields) -> dict:
    """테스트에 쓸 도서를 등록하고 응답 본문을 돌려줍니다."""
    data = {"title": "테스트 도서", "author_id": author_id, "price": 10000} | fields
    response = client.post("/books", json=data, headers=headers)
    assert response.status_code == 201
    return response.json()
