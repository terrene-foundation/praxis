# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.core.session — CO session lifecycle state machine."""

from datetime import datetime, timezone

import pytest


# ---------------------------------------------------------------------------
# SessionState enum
# ---------------------------------------------------------------------------


class TestSessionState:
    """Test the SessionState enum values and type."""

    def test_all_states_exist(self):
        from praxis.core.session import SessionState

        assert SessionState.CREATING == "creating"
        assert SessionState.ACTIVE == "active"
        assert SessionState.PAUSED == "paused"
        assert SessionState.ARCHIVED == "archived"

    def test_session_state_is_str_enum(self):
        from praxis.core.session import SessionState

        assert isinstance(SessionState.ACTIVE, str)
        assert SessionState.ACTIVE == "active"

    def test_all_four_states_defined(self):
        from praxis.core.session import SessionState

        members = list(SessionState)
        assert len(members) == 4


# ---------------------------------------------------------------------------
# VALID_TRANSITIONS
# ---------------------------------------------------------------------------


class TestValidTransitions:
    """Test the state transition table."""

    def test_creating_can_transition_to_active(self):
        from praxis.core.session import VALID_TRANSITIONS, SessionState

        assert SessionState.ACTIVE in VALID_TRANSITIONS[SessionState.CREATING]

    def test_active_can_transition_to_paused(self):
        from praxis.core.session import VALID_TRANSITIONS, SessionState

        assert SessionState.PAUSED in VALID_TRANSITIONS[SessionState.ACTIVE]

    def test_active_can_transition_to_archived(self):
        from praxis.core.session import VALID_TRANSITIONS, SessionState

        assert SessionState.ARCHIVED in VALID_TRANSITIONS[SessionState.ACTIVE]

    def test_paused_can_transition_to_active(self):
        from praxis.core.session import VALID_TRANSITIONS, SessionState

        assert SessionState.ACTIVE in VALID_TRANSITIONS[SessionState.PAUSED]

    def test_paused_can_transition_to_archived(self):
        from praxis.core.session import VALID_TRANSITIONS, SessionState

        assert SessionState.ARCHIVED in VALID_TRANSITIONS[SessionState.PAUSED]

    def test_archived_is_terminal(self):
        from praxis.core.session import VALID_TRANSITIONS, SessionState

        assert VALID_TRANSITIONS[SessionState.ARCHIVED] == set()

    def test_creating_cannot_go_to_paused(self):
        from praxis.core.session import VALID_TRANSITIONS, SessionState

        assert SessionState.PAUSED not in VALID_TRANSITIONS[SessionState.CREATING]

    def test_creating_cannot_go_to_archived(self):
        from praxis.core.session import VALID_TRANSITIONS, SessionState

        assert SessionState.ARCHIVED not in VALID_TRANSITIONS[SessionState.CREATING]


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class TestCustomExceptions:
    """Test that custom exceptions are properly defined."""

    def test_invalid_state_transition_error_exists(self):
        from praxis.core.session import InvalidStateTransitionError

        err = InvalidStateTransitionError("active -> creating")
        assert "active -> creating" in str(err)

    def test_session_not_active_error_exists(self):
        from praxis.core.session import SessionNotActiveError

        err = SessionNotActiveError("Session is paused")
        assert "paused" in str(err)


# ---------------------------------------------------------------------------
# SessionManager.create_session
# ---------------------------------------------------------------------------


class TestCreateSession:
    """Test session creation with the SessionManager."""

    def test_create_session_returns_dict(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        assert isinstance(session, dict)

    def test_create_session_has_session_id(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        assert "session_id" in session
        assert len(session["session_id"]) > 0

    def test_create_session_state_is_active(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        assert session["state"] == "active"

    def test_create_session_stores_workspace_id(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-abc")
        assert session["workspace_id"] == "ws-abc"

    def test_create_session_default_domain_is_coc(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        assert session["domain"] == "coc"

    def test_create_session_custom_domain(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001", domain="coe")
        assert session["domain"] == "coe"

    def test_create_session_has_created_at(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        assert "created_at" in session
        assert session["created_at"].endswith("Z")

    def test_create_session_has_updated_at(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        assert "updated_at" in session

    def test_create_session_ended_at_is_none(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        assert session["ended_at"] is None

    def test_create_session_has_constraint_envelope(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        assert "constraint_envelope" in session
        assert isinstance(session["constraint_envelope"], dict)

    def test_create_session_with_custom_constraints(self, key_manager, sample_constraints):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-001",
            constraints=sample_constraints,
        )
        assert session["constraint_envelope"] == sample_constraints

    def test_create_session_generates_genesis_with_key_manager(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        # When key_manager is available, genesis_id should be populated
        assert session["genesis_id"] is not None
        assert len(session["genesis_id"]) > 0

    def test_create_session_without_key_manager(self):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=None)
        session = mgr.create_session(workspace_id="ws-001")
        assert session["genesis_id"] is None

    def test_create_session_has_metadata(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        assert "metadata" in session
        assert isinstance(session["metadata"], dict)

    def test_create_session_unique_ids(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        s1 = mgr.create_session(workspace_id="ws-001")
        s2 = mgr.create_session(workspace_id="ws-001")
        assert s1["session_id"] != s2["session_id"]

    def test_create_session_empty_workspace_id_raises(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        with pytest.raises(ValueError, match="workspace_id"):
            mgr.create_session(workspace_id="")


# ---------------------------------------------------------------------------
# SessionManager.get_session
# ---------------------------------------------------------------------------


class TestGetSession:
    """Test session retrieval."""

    def test_get_session_returns_created_session(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        created = mgr.create_session(workspace_id="ws-001")
        fetched = mgr.get_session(created["session_id"])
        assert fetched["session_id"] == created["session_id"]
        assert fetched["state"] == created["state"]

    def test_get_session_not_found_raises_key_error(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        with pytest.raises(KeyError, match="nonexistent"):
            mgr.get_session("nonexistent")


# ---------------------------------------------------------------------------
# SessionManager state transitions
# ---------------------------------------------------------------------------


class TestPauseSession:
    """Test pausing an active session."""

    def test_pause_active_session_succeeds(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        paused = mgr.pause_session(session["session_id"], reason="lunch break")
        assert paused["state"] == "paused"

    def test_pause_session_stores_reason_in_metadata(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        paused = mgr.pause_session(session["session_id"], reason="meeting")
        assert paused["metadata"].get("pause_reason") == "meeting"

    def test_pause_archived_session_raises(self, key_manager):
        from praxis.core.session import InvalidStateTransitionError, SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        mgr.end_session(session["session_id"])
        with pytest.raises(InvalidStateTransitionError):
            mgr.pause_session(session["session_id"])

    def test_pause_already_paused_session_raises(self, key_manager):
        from praxis.core.session import InvalidStateTransitionError, SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        mgr.pause_session(session["session_id"])
        with pytest.raises(InvalidStateTransitionError):
            mgr.pause_session(session["session_id"])

    def test_pause_updates_updated_at(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        paused = mgr.pause_session(session["session_id"])
        assert paused["updated_at"] >= session["updated_at"]


class TestResumeSession:
    """Test resuming a paused session."""

    def test_resume_paused_session_succeeds(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        mgr.pause_session(session["session_id"])
        resumed = mgr.resume_session(session["session_id"])
        assert resumed["state"] == "active"

    def test_resume_active_session_raises(self, key_manager):
        from praxis.core.session import InvalidStateTransitionError, SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        with pytest.raises(InvalidStateTransitionError):
            mgr.resume_session(session["session_id"])

    def test_resume_archived_session_raises(self, key_manager):
        from praxis.core.session import InvalidStateTransitionError, SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        mgr.end_session(session["session_id"])
        with pytest.raises(InvalidStateTransitionError):
            mgr.resume_session(session["session_id"])


class TestEndSession:
    """Test ending (archiving) a session."""

    def test_end_active_session_succeeds(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        ended = mgr.end_session(session["session_id"], summary="done")
        assert ended["state"] == "archived"

    def test_end_paused_session_succeeds(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        mgr.pause_session(session["session_id"])
        ended = mgr.end_session(session["session_id"])
        assert ended["state"] == "archived"

    def test_end_session_sets_ended_at(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        ended = mgr.end_session(session["session_id"])
        assert ended["ended_at"] is not None
        assert ended["ended_at"].endswith("Z")

    def test_end_session_stores_summary(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        ended = mgr.end_session(session["session_id"], summary="Completed feature X")
        assert ended["metadata"].get("summary") == "Completed feature X"

    def test_end_archived_session_raises(self, key_manager):
        from praxis.core.session import InvalidStateTransitionError, SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001")
        mgr.end_session(session["session_id"])
        with pytest.raises(InvalidStateTransitionError):
            mgr.end_session(session["session_id"])


# ---------------------------------------------------------------------------
# SessionManager.list_sessions
# ---------------------------------------------------------------------------


class TestListSessions:
    """Test listing and filtering sessions."""

    def test_list_all_sessions(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        mgr.create_session(workspace_id="ws-001")
        mgr.create_session(workspace_id="ws-002")
        sessions = mgr.list_sessions()
        assert len(sessions) == 2

    def test_list_sessions_filter_by_workspace(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        mgr.create_session(workspace_id="ws-001")
        mgr.create_session(workspace_id="ws-002")
        mgr.create_session(workspace_id="ws-001")
        sessions = mgr.list_sessions(workspace_id="ws-001")
        assert len(sessions) == 2
        assert all(s["workspace_id"] == "ws-001" for s in sessions)

    def test_list_sessions_filter_by_state(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        s1 = mgr.create_session(workspace_id="ws-001")
        mgr.create_session(workspace_id="ws-001")
        mgr.pause_session(s1["session_id"])
        sessions = mgr.list_sessions(state="paused")
        assert len(sessions) == 1
        assert sessions[0]["state"] == "paused"

    def test_list_sessions_empty_result(self, key_manager):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        sessions = mgr.list_sessions()
        assert sessions == []


# ---------------------------------------------------------------------------
# SessionManager.update_constraints
# ---------------------------------------------------------------------------


class TestUpdateConstraints:
    """Test constraint envelope updates on sessions."""

    def test_update_constraints_tightening_succeeds(self, key_manager, sample_constraints):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-001",
            constraints=sample_constraints,
        )
        tighter = {
            "financial": {"max_spend": 500.0},
            "operational": {"allowed_actions": ["read", "write"]},
            "temporal": {"max_duration_minutes": 60},
            "data_access": {"allowed_paths": ["/src", "/tests"]},
            "communication": {"allowed_channels": ["internal"]},
        }
        updated = mgr.update_constraints(session["session_id"], tighter)
        assert updated["constraint_envelope"]["financial"]["max_spend"] == 500.0

    def test_update_constraints_loosening_raises(self, key_manager, sample_constraints):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-001",
            constraints=sample_constraints,
        )
        looser = {
            "financial": {"max_spend": 2000.0},
            "operational": {"allowed_actions": ["read", "write", "execute", "deploy"]},
            "temporal": {"max_duration_minutes": 240},
            "data_access": {"allowed_paths": ["/src", "/tests", "/docs", "/secrets"]},
            "communication": {"allowed_channels": ["internal", "email", "external"]},
        }
        with pytest.raises(ValueError, match="[Ll]oosen|[Tt]ighten"):
            mgr.update_constraints(session["session_id"], looser)

    def test_update_constraints_on_archived_session_raises(self, key_manager, sample_constraints):
        from praxis.core.session import SessionNotActiveError, SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-001",
            constraints=sample_constraints,
        )
        mgr.end_session(session["session_id"])
        with pytest.raises(SessionNotActiveError):
            mgr.update_constraints(session["session_id"], sample_constraints)

    def test_update_constraints_updates_updated_at(self, key_manager, sample_constraints):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-001",
            constraints=sample_constraints,
        )
        tighter = {
            "financial": {"max_spend": 500.0},
            "operational": {"allowed_actions": ["read"]},
            "temporal": {"max_duration_minutes": 60},
            "data_access": {"allowed_paths": ["/src"]},
            "communication": {"allowed_channels": ["internal"]},
        }
        updated = mgr.update_constraints(session["session_id"], tighter)
        assert updated["updated_at"] >= session["updated_at"]


# ---------------------------------------------------------------------------
# Full lifecycle integration
# ---------------------------------------------------------------------------


class TestFullLifecycle:
    """Test complete session lifecycle: create -> pause -> resume -> end."""

    def test_full_lifecycle(self, key_manager, sample_constraints):
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")

        # Create
        session = mgr.create_session(
            workspace_id="ws-001",
            domain="coc",
            constraints=sample_constraints,
        )
        assert session["state"] == "active"

        sid = session["session_id"]

        # Pause
        paused = mgr.pause_session(sid, reason="break")
        assert paused["state"] == "paused"

        # Resume
        resumed = mgr.resume_session(sid)
        assert resumed["state"] == "active"

        # End
        ended = mgr.end_session(sid, summary="Complete")
        assert ended["state"] == "archived"
        assert ended["ended_at"] is not None


# ---------------------------------------------------------------------------
# Domain YAML constraint template integration (M02-01)
# ---------------------------------------------------------------------------


class TestDomainYamlConstraintResolution:
    """SessionManager should resolve constraint templates from domain YAML files."""

    def test_coe_year1_from_domain_yaml(self, key_manager):
        """Creating a session with domain='coe', template='year1' should use the
        COE domain YAML template, not the hardcoded CONSTRAINT_TEMPLATES."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-edu",
            domain="coe",
            constraint_template="year1",
        )
        envelope = session["constraint_envelope"]

        # These values come from coe/domain.yml year1, NOT hardcoded templates
        assert envelope["financial"]["max_spend"] == 5.0
        assert envelope["operational"]["allowed_actions"] == ["read", "search"]
        assert envelope["operational"]["max_actions_per_hour"] == 50
        assert envelope["temporal"]["max_duration_minutes"] == 90
        assert envelope["data_access"]["allowed_paths"] == ["/course/"]
        assert envelope["communication"]["allowed_channels"] == ["internal"]

    def test_coe_year1_has_runtime_fields_injected(self, key_manager):
        """Domain YAML templates should have runtime fields (current_spend,
        elapsed_minutes, blocked_* lists) injected during normalization."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-edu",
            domain="coe",
            constraint_template="year1",
        )
        envelope = session["constraint_envelope"]

        # Runtime fields should be present with zero/empty defaults
        assert envelope["financial"]["current_spend"] == 0.0
        assert envelope["temporal"]["elapsed_minutes"] == 0
        assert envelope["operational"]["blocked_actions"] == []
        assert envelope["data_access"]["blocked_paths"] == []
        assert envelope["communication"]["blocked_channels"] == []

    def test_coc_moderate_from_domain_yaml(self, key_manager):
        """COC domain has matching template names as the hardcoded defaults,
        but domain YAML values should take priority."""
        from praxis.core.session import CONSTRAINT_TEMPLATES, SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-dev",
            domain="coc",
            constraint_template="moderate",
        )
        envelope = session["constraint_envelope"]

        # COC domain YAML moderate has max_spend=50.0
        # Hardcoded moderate has max_spend=100.0
        # Domain YAML should win
        assert envelope["financial"]["max_spend"] == 50.0

        # Verify this is different from the hardcoded template
        hardcoded_moderate = CONSTRAINT_TEMPLATES["moderate"]
        assert hardcoded_moderate["financial"]["max_spend"] == 100.0

    def test_coc_strict_from_domain_yaml(self, key_manager):
        """COC strict template from YAML should include max_actions_per_hour
        which the hardcoded template does not have."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-dev",
            domain="coc",
            constraint_template="strict",
        )
        envelope = session["constraint_envelope"]

        # COC YAML strict has max_actions_per_hour which hardcoded doesn't
        assert envelope["operational"]["max_actions_per_hour"] == 100

    def test_explicit_constraints_override_domain_yaml(self, key_manager, sample_constraints):
        """Explicit constraints parameter should always win over domain YAML."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-edu",
            domain="coe",
            constraint_template="year1",
            constraints=sample_constraints,
        )
        # sample_constraints has max_spend=1000.0, not COE year1's 5.0
        assert session["constraint_envelope"]["financial"]["max_spend"] == 1000.0

    def test_unknown_template_falls_back_to_hardcoded(self, key_manager):
        """If domain YAML doesn't have the requested template but the hardcoded
        dict does, fall back to hardcoded."""
        from praxis.core.session import SessionManager

        # COE domain has year1/year2/year3 but NOT 'moderate'
        # Hardcoded templates DO have 'moderate'
        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-edu",
            domain="coe",
            constraint_template="moderate",
        )
        envelope = session["constraint_envelope"]

        # Should get hardcoded moderate values
        assert envelope["financial"]["max_spend"] == 100.0

    def test_unknown_template_and_no_hardcoded_raises(self, key_manager):
        """If neither domain YAML nor hardcoded templates have the requested
        template, raise ValueError."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        with pytest.raises(ValueError, match="Unknown constraint template"):
            mgr.create_session(
                workspace_id="ws-001",
                domain="coe",
                constraint_template="nonexistent_template",
            )

    def test_cog_advisory_from_domain_yaml(self, key_manager):
        """COG domain should provide advisory template from YAML."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-gov",
            domain="cog",
            constraint_template="advisory",
        )
        envelope = session["constraint_envelope"]

        # Should have all 5 dimensions
        assert "financial" in envelope
        assert "operational" in envelope
        assert "temporal" in envelope
        assert "data_access" in envelope
        assert "communication" in envelope

        # Should have runtime fields injected
        assert envelope["financial"]["current_spend"] == 0.0
        assert envelope["temporal"]["elapsed_minutes"] == 0

    def test_domain_yaml_does_not_mutate_across_sessions(self, key_manager):
        """Creating multiple sessions from the same YAML template should not
        share mutable state between them."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        s1 = mgr.create_session(
            workspace_id="ws-1",
            domain="coe",
            constraint_template="year1",
        )
        s2 = mgr.create_session(
            workspace_id="ws-2",
            domain="coe",
            constraint_template="year1",
        )

        # Mutate s1's envelope in memory — should not affect s2
        s1["constraint_envelope"]["financial"]["current_spend"] = 99.0
        s2_fetched = mgr.get_session(s2["session_id"])
        assert s2_fetched["constraint_envelope"]["financial"]["current_spend"] == 0.0


# ---------------------------------------------------------------------------
# Domain phase definitions integration (M02-04)
# ---------------------------------------------------------------------------


class TestDomainPhaseDefinitions:
    """Sessions should load phase definitions from domain YAML files."""

    def test_coc_session_has_current_phase(self, key_manager):
        """Creating a COC session sets current_phase to the first COC phase."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-dev", domain="coc")
        assert session["current_phase"] == "analyze"

    def test_coe_session_has_current_phase(self, key_manager):
        """Creating a COE session sets current_phase to the first COE phase."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-edu",
            domain="coe",
            constraint_template="year1",
        )
        assert session["current_phase"] == "research"

    def test_cog_session_has_current_phase(self, key_manager):
        """Creating a COG session sets current_phase to the first COG phase."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-gov",
            domain="cog",
            constraint_template="advisory",
        )
        assert session["current_phase"] == "agenda_setting"

    def test_coc_phase_list_matches_domain_yaml(self, key_manager):
        """COC phase_list should match the phases in coc/domain.yml."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-dev", domain="coc")
        assert session["phase_list"] == [
            "analyze",
            "plan",
            "implement",
            "validate",
            "codify",
        ]

    def test_coe_phase_list_matches_domain_yaml(self, key_manager):
        """COE phase_list should match the phases in coe/domain.yml."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-edu",
            domain="coe",
            constraint_template="year1",
        )
        assert session["phase_list"] == ["research", "draft", "review", "revise"]

    def test_cog_phase_list_matches_domain_yaml(self, key_manager):
        """COG phase_list should match the phases in cog/domain.yml."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(
            workspace_id="ws-gov",
            domain="cog",
            constraint_template="advisory",
        )
        assert session["phase_list"] == [
            "agenda_setting",
            "analysis",
            "deliberation",
            "decision",
            "documentation",
        ]

    def test_unknown_domain_has_no_phases(self, key_manager):
        """Sessions with a domain that has no YAML should have current_phase=None."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        # Use a nonexistent domain — will fall back to hardcoded template
        session = mgr.create_session(
            workspace_id="ws-001",
            domain="nonexistent_domain",
            constraint_template="moderate",
        )
        assert session["current_phase"] is None
        assert session["phase_list"] == []

    def test_phase_info_survives_db_roundtrip(self, key_manager):
        """Phase info should be persisted to and restored from the database."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-dev", domain="coc")

        # Fetch from DB
        fetched = mgr.get_session(session["session_id"])
        assert fetched["current_phase"] == "analyze"
        assert fetched["phase_list"] == [
            "analyze",
            "plan",
            "implement",
            "validate",
            "codify",
        ]

    def test_phase_info_survives_pause_resume(self, key_manager):
        """Phase info should be preserved across pause/resume transitions."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-dev", domain="coc")

        paused = mgr.pause_session(session["session_id"], reason="break")
        assert paused["current_phase"] == "analyze"
        assert paused["phase_list"] == [
            "analyze",
            "plan",
            "implement",
            "validate",
            "codify",
        ]

        resumed = mgr.resume_session(session["session_id"])
        assert resumed["current_phase"] == "analyze"
        assert resumed["phase_list"] == [
            "analyze",
            "plan",
            "implement",
            "validate",
            "codify",
        ]

    def test_phase_info_survives_end(self, key_manager):
        """Phase info should be preserved in archived sessions."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-dev", domain="coc")

        ended = mgr.end_session(session["session_id"], summary="done")
        assert ended["current_phase"] == "analyze"
        assert ended["phase_list"] == [
            "analyze",
            "plan",
            "implement",
            "validate",
            "codify",
        ]

    def test_phase_info_in_list_sessions(self, key_manager):
        """list_sessions should include phase info for each session."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        mgr.create_session(workspace_id="ws-dev", domain="coc")
        mgr.create_session(
            workspace_id="ws-edu",
            domain="coe",
            constraint_template="year1",
        )

        sessions = mgr.list_sessions()
        # Find the COC and COE sessions
        coc_session = next(s for s in sessions if s["domain"] == "coc")
        coe_session = next(s for s in sessions if s["domain"] == "coe")

        assert coc_session["current_phase"] == "analyze"
        assert coe_session["current_phase"] == "research"


# ---------------------------------------------------------------------------
# SessionPreconditionError and _verify_preconditions (M10-02)
# ---------------------------------------------------------------------------


class TestSessionPreconditionError:
    """Test the SessionPreconditionError exception."""

    def test_exception_has_checks_failed(self):
        from praxis.core.session import SessionPreconditionError

        err = SessionPreconditionError(
            "failed",
            checks_failed=["genesis_missing", "constraints_incomplete"],
        )
        assert len(err.checks_failed) == 2
        assert "genesis_missing" in err.checks_failed

    def test_exception_default_checks_failed(self):
        from praxis.core.session import SessionPreconditionError

        err = SessionPreconditionError("failed")
        assert err.checks_failed == []


class TestVerifyPreconditions:
    """Test the session-start verification defense-in-depth mechanism."""

    def test_valid_session_passes_preconditions(self, key_manager):
        """Creating a normal session should pass all precondition checks."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        session = mgr.create_session(workspace_id="ws-001", domain="coc")
        # If we got here, preconditions passed
        assert session["state"] == "active"

    def test_session_without_key_manager_passes(self):
        """Sessions without key_manager skip genesis validation."""
        from praxis.core.session import SessionManager

        mgr = SessionManager(key_manager=None)
        session = mgr.create_session(workspace_id="ws-001", domain="coc")
        assert session["state"] == "active"

    def test_incomplete_constraints_detected(self, key_manager):
        """Constraints missing dimensions should be caught by preconditions."""
        from praxis.core.session import SessionManager, SessionPreconditionError

        mgr = SessionManager(key_manager=key_manager, key_id="test-key")

        # Create with incomplete constraint envelope (missing communication)
        incomplete = {
            "financial": {"max_spend": 100.0},
            "operational": {"allowed_actions": ["read"]},
            "temporal": {"max_duration_minutes": 60},
            "data_access": {"allowed_paths": ["/src"]},
            # communication dimension is missing
        }
        with pytest.raises(SessionPreconditionError, match="constraints_incomplete"):
            mgr.create_session(
                workspace_id="ws-001",
                domain="coc",
                constraints=incomplete,
            )

    def test_all_domains_pass_preconditions(self, key_manager):
        """Every built-in domain should pass precondition checks."""
        from praxis.core.session import SessionManager

        domains_and_templates = [
            ("coc", "moderate"),
            ("coe", "year1"),
            ("cog", "advisory"),
            ("cor", "formal"),
            ("cocomp", "internal"),
            ("cof", "analysis"),
        ]
        mgr = SessionManager(key_manager=key_manager, key_id="test-key")
        for domain, template in domains_and_templates:
            session = mgr.create_session(
                workspace_id=f"ws-{domain}",
                domain=domain,
                constraint_template=template,
            )
            assert (
                session["state"] == "active"
            ), f"Domain '{domain}' with template '{template}' failed"
