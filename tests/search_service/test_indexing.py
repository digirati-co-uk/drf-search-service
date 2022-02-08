import pytest
import requests
from ..utils import is_responsive_404


app_endpoint = "api/search_service"
test_headers = {"Content-Type": "application/json", "Accept": "application/json"}


def test_iiif_instance(http_service, floco_manifest):
    """
    Create a single iiif item that can be used for various tests.

    :return: requests response
    """
    test_endpoint = "iiif"
    identifier = "d8a35385-d097-4306-89c0-1a15aa74e6da"
    image_service = floco_manifest["sequences"][0]["canvases"][0]["images"][0][
        "resource"
    ]["service"]["@id"]
    post_json = {
        "contexts": [  # List of contexts with their id and type
            {"id": "urn:florentinecodex:site:1", "type": "Site"},
            {"id": "FLorentine Codex", "type": "Collection"},
        ],
        "resource": floco_manifest,  # this is the JSON for the IIIF resource
        "id": f"urn:florentinecodex:manifest:{identifier}",  # Madoc ID for the subject/object
        "thumbnail": f"{image_service}/full/400,/0/default.jpg",  # Thumbnail URL
        "cascade": False,
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    j = result.json()
    assert result.status_code == 201
    assert j.get("madoc_id") == f"urn:florentinecodex:manifest:{identifier}"
    assert (
        j.get("madoc_thumbnail")
        == "https://media.getty.edu/iiif/image/124afceb-1051-404a-91fb-df289963b74c/full/400,/0/default.jpg"
    )
    assert j.get("first_canvas_id") is not None
    assert j.get("first_canvas_json") is not None


def test_simple_metadata_query_status(http_service):
    test_endpoint = "search"
    query = {
        "fulltext": "testo manoscritto",
        "contexts": ["urn:florentinecodex:site:1"],
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=query,
        headers=headers,
    )
    assert result.status_code == requests.codes.ok


def test_stripdown_manifests_only(http_service):
    test_endpoint = "iiif"
    identifier = "d8a35385-d097-4306-89c0-1a15aa74e6da"
    madoc_id = f"urn:florentinecodex:manifest:{identifier}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    result = requests.delete(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}/{madoc_id}",
        headers=headers,
    )
    assert result.status_code == 204


def test_iiif_delete(http_service):
    """
    Confirm that the iiif endpoint is empty
    """
    test_endpoint = "iiif"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    result = requests.get(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        headers=headers,
    )
    resp_data = result.json()
    assert result.status_code == requests.codes.ok
    assert resp_data == {
        "pagination": {
            "next": None,
            "page": 1,
            "pageSize": 25,
            "previous": None,
            "totalPages": 1,
            "totalResults": 0,
        },
        "results": [],
    }


def test_iiif_instance_cascade(http_service, floco_manifest):
    """
    Create a single iiif item that can be used for various tests.

    :return: requests response
    """
    test_endpoint = "iiif"
    identifier = "d8a35385-d097-4306-89c0-1a15aa74e6da"
    image_service = floco_manifest["sequences"][0]["canvases"][0]["images"][0][
        "resource"
    ]["service"]["@id"]
    post_json = {
        "contexts": [  # List of contexts with their id and type
            {"id": "urn:florentinecodex:site:1", "type": "Site"},
            {"id": "FLorentine Codex", "type": "Collection"},
        ],
        "resource": floco_manifest,  # this is the JSON for the IIIF resource
        "id": f"urn:florentinecodex:manifest:{identifier}",  # Madoc ID for the subject/object
        "thumbnail": f"{image_service}/full/400,/0/default.jpg",  # Thumbnail URL
        "cascade": True,
        "cascade_canvases": True,
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    j = result.json()
    assert result.status_code == 201
    assert j.get("madoc_id") == f"urn:florentinecodex:manifest:{identifier}"
    assert (
        j.get("madoc_thumbnail")
        == "https://media.getty.edu/iiif/image/124afceb-1051-404a-91fb-df289963b74c/full/400,/0/default.jpg"
    )
    assert j.get("first_canvas_id") is not None
    assert j.get("first_canvas_json") is not None


def test_iiif_count_cascade(http_service, floco_manifest):
    """
    Count should include the manifest, the canvases, and any ranges.
    """
    canvases = len(floco_manifest["sequences"][0]["canvases"])
    ranges = len(floco_manifest["structures"])
    total = canvases + ranges + 1
    test_endpoint = "iiif"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    result = requests.get(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        headers=headers,
    )
    resp_data = result.json()
    assert result.status_code == requests.codes.ok
    assert resp_data["pagination"]["totalResults"] == total  # 1012


def test_indexing_lagq(http_service, lagq):
    """
    Index the Spanish language files into Indexables model
    """
    test_endpoint = "indexables"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    statuses = []
    for post_json in lagq:
        result = requests.post(
            url=f"{http_service}/{app_endpoint}/{test_endpoint}",
            json=post_json,
            headers=headers,
        )
        statuses.append(result.status_code)
    assert all([x == 201 for x in statuses])


def test_spanish_plaintext(http_service):
    """ """
    test_endpoint = "search"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    post_json = {"fulltext": "españoles"}
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    resp_json = result.json()
    assert result.status_code == 200
    assert resp_json["pagination"]["totalResults"] == 5


def test_spanish_plaintext_lemma(http_service):
    """ """
    test_endpoint = "search"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    post_json = {"fulltext": "español"}
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    resp_json = result.json()
    assert result.status_code == 200
    assert resp_json["pagination"]["totalResults"] == 5


def test_indexing_na_en_ad(http_service, na_en_ad):
    """
    Index English language files into Indexables model
    """
    test_endpoint = "indexables"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    statuses = []
    for post_json in na_en_ad:
        result = requests.post(
            url=f"{http_service}/{app_endpoint}/{test_endpoint}",
            json=post_json,
            headers=headers,
        )
        statuses.append(result.status_code)
    assert all([x == 201 for x in statuses])


def test_english_plaintext(http_service):
    """ """
    test_endpoint = "search"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    post_json = {"fulltext": "heavens"}
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    resp_json = result.json()
    assert result.status_code == 200
    assert resp_json["pagination"]["totalResults"] == 3


def test_english_lemma(http_service):
    """ """
    test_endpoint = "search"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    post_json = {"fulltext": "heaven"}
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    resp_json = result.json()
    assert result.status_code == 200
    assert resp_json["pagination"]["totalResults"] == 3


def test_indexing_na_ad(http_service, na_ad):
    """
    Index Nahutal language files into Indexables model
    """
    test_endpoint = "indexables"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    statuses = []
    for post_json in na_ad:
        result = requests.post(
            url=f"{http_service}/{app_endpoint}/{test_endpoint}",
            json=post_json,
            headers=headers,
        )
        statuses.append(result.status_code)
    assert all([x == 201 for x in statuses])


def test_nahuatl_plaintext(http_service):
    """
    This should return 1 result because the text will be token/lemma-tized using the
    simple parser, which will be whitespace delimmited
    """
    test_endpoint = "search"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    post_json = {"fulltext": "ilhujcaiollotitech"}
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    resp_json = result.json()
    assert result.status_code == 200
    assert resp_json["pagination"]["totalResults"] == 1


def test_nahuatl_partialmatch(http_service):
    """
    This should return 1 result because the text will be token/lemma-tized using the
    simple parser, which will be whitespace delimmited

    Then the search_multiple_fields parameter will force an `icontains` match rather than
    a fulltext match
    """
    test_endpoint = "search"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    post_json = {"fulltext": "ilhujcaiollo", "search_multiple_fields": True}
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    resp_json = result.json()
    assert result.status_code == 200
    assert resp_json["pagination"]["totalResults"] == 1


def test_filter_by_language(http_service):
    """
    Should return results when filtering to English but no results when filtering to Nahuatl
    as this is not the Nahuatl form for Moctezuma
    """
    test_endpoint = "search"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    post_json = {"fulltext": "Moctezuma", "language_iso639_2": "eng"}
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    resp_json = result.json()
    assert result.status_code == 200
    assert resp_json["pagination"]["totalResults"] > 0
    post_json = {"fulltext": "Moctezuma", "language_iso639_2": "nci"}
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    resp_json = result.json()
    assert result.status_code == 200
    assert resp_json["pagination"]["totalResults"] == 0


def test_filter_by_group(http_service):
    """
    Should return results when filtering to Anderson and Dibble's English translation
     but no results when filtering to Nahuatl as this is not the Nahuatl form for Moctezuma
    """
    test_endpoint = "search"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    post_json = {
        "fulltext": "Moctezuma",
        "group_id": "na_en|andersondibble",
    }
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    resp_json = result.json()
    assert result.status_code == 200
    assert resp_json["pagination"]["totalResults"] > 0
    post_json = {
        "fulltext": "Moctezuma",
        "group_id": "na|andersondibble",
    }
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    resp_json = result.json()
    assert result.status_code == 200
    assert resp_json["pagination"]["totalResults"] == 0


def test_filter_by_authors(http_service):
    """
    Should return results when filtering to Anderson and Dibble's English translation
    AND the Nahuatl. Check that the number increases when we open it up to both via the
    endswith
    """
    test_endpoint = "search"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    post_json = {
        "fulltext": "Quetzalcoatl",
        "group_id": "na|andersondibble",
    }
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    resp_json = result.json()
    original = resp_json["pagination"]["totalResults"]
    assert original == 4  # We have found some instances of Quetzalcoatl
    post_json = {
        "fulltext": "Quetzalcoatl",
        "raw": {"indexables__group_id__istartswith": "na_en|"},
    }
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    resp_json = result.json()
    new = resp_json["pagination"]["totalResults"]
    assert (
        new == 2
    )  # Less insances of Quetzalcoatl as we are only searching the Nahuatl to English translation
    assert new < original


def test_indexing_tags(http_service, tags):
    """
    Index tags into Indexables model
    """
    test_endpoint = "indexables"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    statuses = []
    for post_json in tags:
        result = requests.post(
            url=f"{http_service}/{app_endpoint}/{test_endpoint}",
            json=post_json,
            headers=headers,
        )
        statuses.append(result.status_code)
    assert all([x == 201 for x in statuses])


def test_find_by_vocab_id(http_service):
    """

    """
    test_endpoint = "search"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    post_json = {"group_id": "10055"}
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    resp_json = result.json()
    assert result.status_code == 200
    assert resp_json["pagination"]["totalResults"] == 2  # 4 genuine tags, but all on same image/canvas + 1 faked one


def test_find_by_vocab_id_lang(http_service):
    """

    """
    test_endpoint = "search"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    post_json = {"group_id": "10055", "language_iso639_2": "spa"}
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    resp_json = result.json()
    assert result.status_code == 200
    assert resp_json["pagination"]["totalResults"] == 1


def test_find_by_term(http_service):
    """

    """
    test_endpoint = "search"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    post_json = {"fulltext": "acatl"}
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    resp_json = result.json()
    assert result.status_code == 200
    assert resp_json["pagination"]["totalResults"] == 2


def test_find_by_term_exact(http_service):
    """

    """
    test_endpoint = "search"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    post_json = {"raw": {
        "indexables__indexable__exact": "Acatl"}}
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    resp_json = result.json()
    assert result.status_code == 200
    assert resp_json["pagination"]["totalResults"] == 1  # Case sensitive search, so only matches 1


def test_find_by_vocab_language(http_service):
    """

    """
    test_endpoint = "search"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    post_json = {"fulltext": "sail", "language_iso639_2": "eng", "type": "tag"}
    result = requests.post(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=headers,
    )
    resp_json = result.json()
    assert result.status_code == 200
    assert resp_json["pagination"]["totalResults"] == 2  # Should be 2 because of stemming
    ids = [x["resource_id"] for x in resp_json["results"]]
    assert "urn:florentinecodex:manifest:d8a35385-d097-4306-89c0-1a15aa74e6da:canvas:823" in ids


def test_iiif_delete_manifest_and_all_canvases(http_service, floco_manifest):
    """
    Delete all of the canvases and the manifests.

    Canvas IDs are just auto-generated from the manifest sequence size, rather than
    fetched via a paginated query
    """
    test_endpoint = "iiif"
    identifier = "d8a35385-d097-4306-89c0-1a15aa74e6da"
    canvases = len(floco_manifest["sequences"][0]["canvases"])
    canvas_list = [
        f"urn:florentinecodex:manifest:{identifier}:canvas:{n}" for n in range(canvases)
    ]
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    statuses = []
    manifest_madoc_id = f"urn:florentinecodex:manifest:{identifier}"
    result = requests.delete(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}/{manifest_madoc_id}",
        headers=headers,
    )
    statuses.append(result.status_code)
    for canvas_id in canvas_list:
        result = requests.delete(
            url=f"{http_service}/{app_endpoint}/{test_endpoint}/{canvas_id}",
            headers=headers,
        )
        statuses.append(result.status_code)
    assert all([x == 204 for x in statuses])


def test_iiif_count_after_delete(http_service, floco_manifest):
    """
    Check that the results after the canvas and manifest delete is just the ranges
    """
    ranges = len(floco_manifest["structures"])
    test_endpoint = "iiif"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    result = requests.get(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        headers=headers,
    )
    resp_data = result.json()
    assert result.status_code == requests.codes.ok
    assert resp_data["pagination"]["totalResults"] == ranges


def test_iiif_fetch_and_delete_remaining(http_service):
    """
    Delete the remaining IIIF resources (these will be ranges only)
    """
    test_endpoint = "iiif"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    result = requests.get(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        headers=headers,
    )
    resp_data = result.json()
    identifiers = [x.get("madoc_id") for x in resp_data["results"]]
    statuses = []
    for identifier in identifiers:
        result = requests.delete(
            url=f"{http_service}/{app_endpoint}/{test_endpoint}/{identifier}",
            headers=headers,
        )
        statuses.append(result.status_code)
    assert all([x == 204 for x in statuses])


def test_iiif_zero(http_service, floco_manifest):
    """
    Check that  there are no IIIF resources
    """
    test_endpoint = "iiif"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    result = requests.get(
        url=f"{http_service}/{app_endpoint}/{test_endpoint}",
        headers=headers,
    )
    resp_data = result.json()
    assert result.status_code == requests.codes.ok
    assert resp_data["pagination"]["totalResults"] == 0
