"""
Unit tests for the Category API endpoints.
Tests cover: list, detail, tree, children, filtering, and model behaviour.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.categories.models import Category

from .factories import CategoryFactory, SubCategoryFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def root_category():
    return CategoryFactory(name="Electronics", is_active=True)


@pytest.fixture
def sub_category(root_category):
    return SubCategoryFactory(name="Phones", parent=root_category, is_active=True)


@pytest.fixture
def inactive_category():
    return CategoryFactory(name="Hidden Category", is_active=False)


@pytest.mark.django_db
class TestCategoryModel:
    """Unit tests for the Category model."""

    def test_slug_auto_generated(self):
        cat = CategoryFactory(name="Home Appliances")
        assert cat.slug == "home-appliances"

    def test_full_path_root(self, root_category):
        assert root_category.full_path == "Electronics"

    def test_full_path_nested(self, root_category, sub_category):
        assert sub_category.full_path == "Electronics > Phones"

    def test_is_root(self, root_category, sub_category):
        assert root_category.is_root is True
        assert sub_category.is_root is False

    def test_depth(self, root_category, sub_category):
        assert root_category.depth == 0
        assert sub_category.depth == 1

    def test_str(self, root_category):
        assert str(root_category) == "Electronics"

    def test_unique_name(self):
        CategoryFactory(name="Unique Cat")
        with pytest.raises(Exception):
            CategoryFactory(name="Unique Cat")

    def test_inactive_not_counted_in_children(self, root_category):
        active_child = SubCategoryFactory(parent=root_category, is_active=True)
        inactive_child = SubCategoryFactory(parent=root_category, is_active=False)
        active_count = root_category.children.filter(is_active=True).count()
        assert active_count == 1


@pytest.mark.django_db
class TestCategoryListAPI:
    """Tests for GET /api/v1/catalog/categories/"""

    def test_list_returns_200(self, api_client, root_category):
        url = reverse("categories:category-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_list_returns_only_active(self, api_client, root_category, inactive_category):
        url = reverse("categories:category-list")
        response = api_client.get(url)
        ids = [c["id"] for c in response.data["results"]]
        assert root_category.id in ids
        assert inactive_category.id not in ids

    def test_list_pagination(self, api_client):
        CategoryFactory.create_batch(25)
        url = reverse("categories:category-list")
        response = api_client.get(url)
        assert "count" in response.data
        assert "results" in response.data
        assert "next" in response.data

    def test_filter_by_name(self, api_client, root_category):
        url = reverse("categories:category-list")
        response = api_client.get(url, {"name": "Elec"})
        assert response.status_code == status.HTTP_200_OK
        assert any("Electronics" in c["name"] for c in response.data["results"])

    def test_filter_root_only(self, api_client, root_category, sub_category):
        url = reverse("categories:category-list")
        response = api_client.get(url, {"root_only": "true"})
        ids = [c["id"] for c in response.data["results"]]
        assert root_category.id in ids
        assert sub_category.id not in ids

    def test_search_by_name(self, api_client, root_category):
        url = reverse("categories:category-list")
        response = api_client.get(url, {"search": "Electro"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1


@pytest.mark.django_db
class TestCategoryDetailAPI:
    """Tests for GET /api/v1/catalog/categories/{id}/"""

    def test_detail_returns_200(self, api_client, root_category):
        url = reverse("categories:category-detail", kwargs={"pk": root_category.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Electronics"

    def test_detail_includes_full_path(self, api_client, sub_category):
        url = reverse("categories:category-detail", kwargs={"pk": sub_category.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert ">" in response.data["full_path"]

    def test_detail_includes_parent(self, api_client, sub_category, root_category):
        url = reverse("categories:category-detail", kwargs={"pk": sub_category.pk})
        response = api_client.get(url)
        assert response.data["parent"]["id"] == root_category.id

    def test_detail_inactive_returns_404(self, api_client, inactive_category):
        url = reverse("categories:category-detail", kwargs={"pk": inactive_category.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_nonexistent_returns_404(self, api_client):
        url = reverse("categories:category-detail", kwargs={"pk": 9999999})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCategoryTreeAPI:
    """Tests for GET /api/v1/catalog/categories/tree/"""

    def test_tree_returns_200(self, api_client, root_category):
        url = reverse("categories:category-tree")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_tree_returns_list(self, api_client, root_category):
        url = reverse("categories:category-tree")
        response = api_client.get(url)
        assert isinstance(response.data, list)

    def test_tree_includes_children(self, api_client, root_category, sub_category):
        url = reverse("categories:category-tree")
        response = api_client.get(url)
        root_in_tree = next(
            (c for c in response.data if c["id"] == root_category.id), None
        )
        assert root_in_tree is not None
        children_ids = [ch["id"] for ch in root_in_tree["children"]]
        assert sub_category.id in children_ids

    def test_tree_excludes_inactive(self, api_client, root_category, inactive_category):
        url = reverse("categories:category-tree")
        response = api_client.get(url)
        ids = [c["id"] for c in response.data]
        assert inactive_category.id not in ids


@pytest.mark.django_db
class TestCategoryChildrenAPI:
    """Tests for GET /api/v1/catalog/categories/{id}/children/"""

    def test_children_returns_200(self, api_client, root_category, sub_category):
        url = reverse("categories:category-children", kwargs={"pk": root_category.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_children_returns_subcategories(self, api_client, root_category, sub_category):
        url = reverse("categories:category-children", kwargs={"pk": root_category.pk})
        response = api_client.get(url)
        ids = [c["id"] for c in response.data]
        assert sub_category.id in ids

    def test_leaf_category_has_empty_children(self, api_client, sub_category):
        url = reverse("categories:category-children", kwargs={"pk": sub_category.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []
