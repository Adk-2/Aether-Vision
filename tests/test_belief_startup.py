from belief import BeliefEngine, MIN_CONSECUTIVE_OBSERVATIONS
from identity import IdentityResolver
from evaluation.scenarios.common import track, BASE_TIME
from evaluation.scenarios.reasoning_accuracy import _rules
from events import EventEngine, EventFilter
from memory import MemoryEngine
from timeline import Timeline
from knowledge import KnowledgeEngine
from reasoning import ReasoningEngine
from planning import Planner, PlannerRules, Goal
from scene import SceneGraph
from world import WorldState
from pipeline import PerceptionPipeline


def identity(label="cup", track_id=1):
    return IdentityResolver().update([track(label, track_id=track_id)])[0]


def test_belief_is_unpublished_until_consistent_threshold():
    engine = BeliefEngine()
    for _ in range(MIN_CONSECUTIVE_OBSERVATIONS - 1):
        assert engine.update([identity()]) == []
        assert engine.all() == [] and engine.get(1) is None
    states = engine.update([identity()])
    assert len(states) == 1
    assert states[0].current_belief == "cup"
    assert states[0].frames_stable == 1  # lifetime counts published frames


def test_label_change_and_missing_frame_reset_pending_streak():
    engine = BeliefEngine()
    for _ in range(MIN_CONSECUTIVE_OBSERVATIONS - 1):
        engine.update([identity()])
    assert engine.update([identity("bottle")]) == []
    engine.update([])
    for _ in range(MIN_CONSECUTIVE_OBSERVATIONS - 1):
        assert engine.update([identity("bottle")]) == []
    assert engine.update([identity("bottle")])[0].current_belief == "bottle"


def test_pending_tracks_are_independent_and_restore_clears_pending():
    engine = BeliefEngine()
    for i in range(MIN_CONSECUTIVE_OBSERVATIONS):
        states = engine.update([identity(), identity("cup" if i % 2 else "bottle", 2)])
    assert [s.track_id for s in states] == [1]
    engine.replace_all([])
    assert engine.update([identity()]) == []


def test_memory_knowledge_reasoning_planning_work_before_belief_exists():
    beliefs, resolver = BeliefEngine(), IdentityResolver()
    memory, timeline, world = MemoryEngine(), Timeline(), WorldState()
    events, event_filter = EventEngine(), EventFilter()
    knowledge = KnowledgeEngine(memory, timeline, SceneGraph(), beliefs)
    reasoning = ReasoningEngine(knowledge, _rules())
    planner = Planner(knowledge, reasoning, PlannerRules())
    for i in range(MIN_CONSECUTIVE_OBSERVATIONS):
        tracks = [track("cup", frame_index=i, center=(10, 20))]
        states = beliefs.update(resolver.update(tracks))
        PerceptionPipeline._apply_beliefs(tracks, states)
        snapshot = world.update(tracks, tracks[0].last_seen)
        generated = event_filter.filter_events(
            events.generate_events(world.previous_snapshot, snapshot)
        )
        memory.process(generated)
        timeline.process(generated)
        knowledge.use_visible_track_ids({1})
        assert memory.store.get_by_track_id(1) is not None
        assert knowledge.where_is("cup").result == (10, 20)
        assert knowledge.current_state("cup").success
        assert knowledge.current_belief("cup").success == (
            i == MIN_CONSECUTIVE_OBSERVATIONS - 1
        )
        reasoning.infer("cup")
        plan = planner.create_plan(Goal("find", "cup", 1, BASE_TIME))
        assert [a.description for a in plan.actions] == [
            "Inspect last known location (10, 20)."
        ]
    assert knowledge.current_belief("cup").result == "cup"
