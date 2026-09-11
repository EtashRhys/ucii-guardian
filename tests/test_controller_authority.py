"""Tests for Guardian's protected controller-authority loading boundary."""

from __future__ import annotations

import inspect

import pytest

import ucii_guardian.controller_authority as controller
from ucii_guardian.controller_authority import (
    GuardianControllerAuthorityError,
    default_controller_authority_path,
    load_controller_authority,
)


def test_default_controller_authority_path_is_user_local(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv(
        "LOCALAPPDATA",
        str(tmp_path),
    )

    assert default_controller_authority_path() == (
        tmp_path
        / "UCII"
        / "Guardian"
        / "authority"
        / "controller-authority-v1"
    )


def test_default_path_fails_closed_without_localappdata(
    monkeypatch,
):
    monkeypatch.delenv(
        "LOCALAPPDATA",
        raising=False,
    )

    with pytest.raises(
        GuardianControllerAuthorityError,
        match="LOCALAPPDATA",
    ):
        default_controller_authority_path()


def test_loader_reads_existing_secret_and_hardens_boundary(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "controller-authority-v1"

    path.write_text(
        "controller-secret-value\n",
        encoding="utf-8",
    )

    hardened = []

    monkeypatch.setattr(
        controller,
        "_harden_private_path",
        lambda target, *, directory: hardened.append(
            (
                target,
                directory,
            )
        ),
    )

    secret = load_controller_authority(
        path
    )

    assert secret == "controller-secret-value"

    assert hardened == [
        (
            path.parent,
            True,
        ),
        (
            path,
            False,
        ),
    ]


def test_loader_fails_closed_when_file_is_missing(
    tmp_path,
):
    with pytest.raises(
        GuardianControllerAuthorityError,
        match="does not exist",
    ):
        load_controller_authority(
            tmp_path / "missing"
        )


@pytest.mark.parametrize(
    "contents",
    (
        b"",
        b" ",
        b"\n",
        b"\r\n\t ",
    ),
)
def test_loader_rejects_empty_or_whitespace_secret(
    tmp_path,
    monkeypatch,
    contents,
):
    path = tmp_path / "controller-authority-v1"
    path.write_bytes(
        contents
    )

    monkeypatch.setattr(
        controller,
        "_harden_private_path",
        lambda path, *, directory: None,
    )

    with pytest.raises(
        GuardianControllerAuthorityError,
        match="non-empty",
    ):
        load_controller_authority(
            path
        )


def test_loader_rejects_invalid_utf8(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "controller-authority-v1"
    path.write_bytes(
        b"\xff\xfe\xfd"
    )

    monkeypatch.setattr(
        controller,
        "_harden_private_path",
        lambda path, *, directory: None,
    )

    with pytest.raises(
        GuardianControllerAuthorityError,
        match="valid UTF-8",
    ):
        load_controller_authority(
            path
        )


def test_loader_rejects_nul_data(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "controller-authority-v1"
    path.write_bytes(
        b"controller\x00authority"
    )

    monkeypatch.setattr(
        controller,
        "_harden_private_path",
        lambda path, *, directory: None,
    )

    with pytest.raises(
        GuardianControllerAuthorityError,
        match="invalid data",
    ):
        load_controller_authority(
            path
        )


def test_loader_does_not_create_missing_secret(
    tmp_path,
):
    path = tmp_path / "controller-authority-v1"

    with pytest.raises(
        GuardianControllerAuthorityError
    ):
        load_controller_authority(
            path
        )

    assert not path.exists()


def test_controller_authority_module_has_no_public_secret_persistence():
    source = inspect.getsource(
        controller
    )

    prohibited = (
        "write_text(",
        "write_bytes(",
        "NamedTemporaryFile",
        "os.link(",
        "UCIIClient(",
        "revoke_delegated(",
    )

    for value in prohibited:
        assert value not in source


def test_controller_authority_module_has_no_ucii_server_internal_imports():
    source = inspect.getsource(
        controller
    )

    prohibited = (
        "from pq_auth",
        "import pq_auth",
        "from fastapi",
        "import fastapi",
        "from sqlalchemy",
        "import sqlalchemy",
    )

    for value in prohibited:
        assert value not in source
