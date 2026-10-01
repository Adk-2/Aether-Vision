# Project Aether

### A Layered Computer Vision System for Perception, Memory, Reasoning, and World Understanding

Project Aether is an experimental **real-time visual perception system** designed to move beyond simple object detection.

Instead of treating every camera frame as an isolated prediction, Aether maintains a continuously evolving representation of the world.

It detects objects, tracks them across frames, stabilizes uncertain labels, maintains object identity, records events, stores memories, constructs spatial relationships, maintains beliefs, performs deterministic reasoning, generates search plans, and provides a queryable assistant interface.

The system is built around the following idea:

> **Camera → Perception → Tracking → Memory → World Model → Reasoning → Planning**

---

# Overview

Traditional object detection answers questions such as:

> "What objects are in this frame?"

Aether attempts to answer higher-level questions such as:

```text
What objects are currently visible?
```

```text
Where was the bottle last seen?
```

```text
What happened to the object?
```

```text
What objects are near the person?
```

```text
Is the object currently visible?
```

```text
How should I search for the missing object?
```

The system therefore treats vision as a **continuous perception problem**, rather than a sequence of independent detections.

---

# Core Architecture

Aether is organized into multiple layers, each responsible for a specific aspect of world understanding.

```text
┌─────────────────────────────────────────────────────────────┐
│                         CAMERA                              │
│                     OpenCV Capture                          │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         VISION                              │
│                    YOLO Object Detection                    │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        TRACKING                             │
│              Persistent Object Track IDs                    │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  IDENTITY + BELIEF                          │
│       Label History • Confidence • Belief Stability          │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       WORLD STATE                           │
│                 Current Object Registry                     │
└─────────────────────────────┬───────────────────────────────┘
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
          ┌────────────┐ ┌──────────┐ ┌─────────────┐
          │   SCENE    │ │  EVENTS  │ │   MEMORY    │
          │   GRAPH    │ │  ENGINE  │ │  + TIMELINE │
          └─────┬──────┘ └────┬─────┘ └──────┬──────┘
                │             │              │
                └─────────────┼──────────────┘
                              ▼
                    ┌──────────────────┐
                    │ KNOWLEDGE ENGINE │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ REASONING ENGINE │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │     PLANNER      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │    ASSISTANT     │
                    └──────────────────┘
```

---

# Perception Pipeline

Each camera frame passes through a deterministic multi-stage pipeline.

```text
Frame
 ↓
YOLO Inference
 ↓
Detection Adapter
 ↓
Confidence Filter
 ↓
Object Tracker
 ↓
Temporal Detection Stabilizer
 ↓
Identity Resolver
 ↓
Belief Engine
 ↓
World State
 ↓
Scene Graph
 ↓
Event Engine
 ↓
Memory
 ↓
Timeline
 ↓
Knowledge
 ↓
Reasoning
 ↓
Planning
```

This entire cycle is implemented by `PerceptionPipeline`.

---

# 👁️ Vision Layer

Aether uses **YOLOv8 Nano** as its default object detector.

Model:

```text
yolov8n.pt
```

The detector is isolated behind a dedicated `VisionDetector` abstraction.

```python
VisionDetector.detect(frame)
```

The detector produces raw YOLO inference results, which are converted into Aether's internal `Detection` representation.

This separation keeps the rest of the system independent from the underlying detection framework.

---

# Detection Representation

Raw model predictions are converted into canonical detection objects containing information such as:

* Object class
* Confidence
* Bounding box
* Center position
* Timestamp

Conceptually:

```text
YOLO Result
     ↓
Detection
 ├── class_name
 ├── confidence
 ├── bounding_box
 ├── center
 └── timestamp
```

This creates a stable interface between computer vision and the rest of the architecture.

---

# 🎯 Confidence Filtering

Not every raw detector prediction is accepted.

A confidence filtering layer removes predictions below the configured confidence threshold.

```text
Raw detections
      ↓
Confidence Filter
      ↓
Trusted detections
```

This prevents very weak predictions from immediately entering the tracking and world-model layers.

---

# 🔄 Object Tracking

Aether maintains persistent object identities across frames.

Instead of treating:

```text
Frame 1 → bottle
Frame 2 → bottle
Frame 3 → bottle
```

as three unrelated detections, the tracker attempts to represent them as:

```text
Track #001
 ├── Frame 1
 ├── Frame 2
 └── Frame 3
```

The current tracker uses nearest-neighbour association based on object-center distance.

Default association threshold:

```text
50 pixels
```

The tracker maintains:

* Track ID
* Current detection
* Track history
* Missed frames
* Active/inactive state

---

# 🧠 Temporal Detection Stabilization

Object detectors can produce noisy labels.

For example:

```text
Frame 1 → bottle
Frame 2 → cup
Frame 3 → bottle
Frame 4 → bottle
```

Aether does not immediately accept every label change.

The `DetectionStabilizer` maintains label history per track and uses a stabilization policy before changing the currently stable label.

Conceptually:

```text
Raw predictions
      ↓
Label history
      ↓
Voting / temporal evidence
      ↓
Stable label
```

This reduces frame-to-frame label flickering.

---

# 🪪 Identity Resolution

The identity layer maintains a persistent semantic identity for each track.

An identity contains information such as:

* Track ID
* Current label
* Confidence
* Label history
* Last update time

Identity is therefore separated from the raw detector output.

```text
Detection
    ↓
Track
    ↓
Identity
```

This allows downstream systems to reason about persistent objects instead of individual detections.

---

# 🧠 Belief Engine

Aether contains a separate belief layer for maintaining confidence in object identity.

The belief engine does not immediately switch beliefs whenever a detector produces a different label.

A challenger label must satisfy stability conditions before replacing the existing belief.

Current policy includes:

```text
Minimum consecutive observations: 10
Minimum confidence margin:       0.20
Belief decay:                     0.98
Minimum belief confidence:        0.05
```

This creates a conservative belief transition mechanism.

Example:

```text
Current belief:
bottle — 0.84

New observations:
cup — 0.61
cup — 0.63
cup — 0.68
...

↓

Do not immediately switch.

↓

Require persistent evidence.

↓

Potential belief transition:
bottle → cup
```

---

# 🌍 World State

The `WorldState` layer maintains the current and previous snapshots of active tracks.

A world snapshot provides a representation of what Aether currently believes is present in the scene.

```text
WorldSnapshot
 ├── timestamp
 └── active tracks
```

The previous snapshot is used by the event engine to determine what changed between frames.

---

# 🕸️ Scene Graph

Aether constructs a lightweight scene graph from tracked object geometry.

Supported spatial relationships include:

```text
LEFT_OF
RIGHT_OF
ABOVE
BELOW
NEAR
OVERLAPS
```

The current scene graph is geometry-driven rather than language-model-driven.

For example:

```text
Person_001
      │
      ├── NEAR ──► Bottle_002
      │
      └── LEFT_OF ──► Chair_003
```

The default `NEAR` distance threshold is:

```text
150 pixels
```

This provides structured spatial knowledge for downstream reasoning and queries.

---

# ⚡ Event Engine

Aether compares consecutive world snapshots to identify changes.

Supported event types include events such as:

* Appeared
* Disappeared
* Moved
* Stopped
* Started moving
* Stopped moving
* Removed
* Taken
* Picked up
* Destroyed
* Broken

For example:

```text
Frame N:
Bottle_001 exists at (300, 250)

Frame N+1:
Bottle_001 exists at (340, 250)

↓

Event:
Bottle_001 MOVED
```

If an object disappears from the next snapshot:

```text
Frame N:
Bottle_001 visible

Frame N+1:
Bottle_001 missing

↓

Event:
Bottle_001 DISAPPEARED
```

---

# 🧹 Event Filtering

Raw event generation can produce noisy movement events.

Aether includes an `EventFilter` layer to suppress events that do not provide useful information.

The pipeline also maintains movement-noise suppression state.

This creates a distinction between:

```text
Raw perception changes
```

and:

```text
Meaningful world events
```

---

# 🧠 Working Memory

Events are converted into structured memory records.

Memory tracks the state of objects over time.

Possible object states include concepts such as:

```text
ACTIVE
MOVING
STATIC
LOST
```

A memory record can retain information such as:

* Object name
* Track ID
* Current status
* Last position
* First seen time
* Last seen time
* Confidence
* Historical observations

This gives Aether a short-term world memory rather than relying solely on the current frame.

---

# ⏳ Timeline

The timeline layer converts events into chronological entries.

Example:

```text
12:01:03  bottle_001 APPEARED
12:01:05  bottle_001 MOVED
12:01:08  bottle_001 STOPPED
12:01:12  bottle_001 DISAPPEARED
```

The timeline provides an episodic representation of what happened.

It is later used by the knowledge and assistant layers.

---

# 💾 Persistent Memory

Aether can persist selected memory information to:

```text
data/aether_memory.json
```

The persistence layer:

* Saves memory
* Loads memory
* Clears memory
* Writes atomically
* Recovers from invalid/missing files
* Compacts persistent memory

This allows information about previously observed objects to survive application restarts.

---

# 🧩 Knowledge Engine

The Knowledge Engine acts as a unified query layer over multiple internal knowledge sources.

It combines:

```text
Working Memory
Current Observation
Persistent Memory
Timeline
Scene Graph
Belief Engine
```

Supported knowledge queries include:

```text
WHERE_IS
WHAT_HAPPENED
OBJECTS_NEAR
CURRENT_BELIEF
CURRENT_STATE
```

The engine also tracks the source modules responsible for each result.

This allows downstream reasoning to distinguish between current observations and historical information.

---

# 🔬 Reasoning Engine

Aether includes a deterministic rule-based reasoning system.

The reasoning engine collects facts from the Knowledge Engine and evaluates registered rules.

It can reason about concepts such as:

* Object movement
* Object disappearance
* Nearby people
* Removal evidence
* Destruction evidence
* Recent movement
* Object relationships

The reasoning system supports iterative inference:

```text
Known Facts
    ↓
Rule Evaluation
    ↓
New Conclusions
    ↓
Evaluate Again
    ↓
Additional Conclusions
```

This provides a small forward-chaining reasoning mechanism without requiring an LLM.

---

# 🧭 Planning

The planner converts knowledge and reasoning into explainable actions.

Current planning rules include:

### Known Location

If the target object has a known location:

```text
Inspect last known location.
```

### Nearby Evidence

If nearby objects provide useful evidence:

```text
Search near <object>.
```

### No Evidence

If there is insufficient evidence:

```text
Expand search area.
```

Each proposed action has:

* Description
* Priority
* Reason

The planner **proposes actions but does not execute them**.

---

# 🤖 Aether Assistant

Aether contains a deterministic assistant that exposes the system's internal knowledge through natural-language queries.

Supported query categories include:

```text
Where is <object>?
```

```text
Where was <object>?
```

```text
What happened to <object>?
```

```text
What is near <object>?
```

```text
How do I find <object>?
```

The assistant combines:

```text
Knowledge
+
Reasoning
+
Planning
```

to produce an answer.

Example:

```text
User:
Where is the bottle?

Aether:
The bottle was last observed at approximately
(421, 286).

Planning:
Inspect last known location.
```

The assistant deliberately avoids inventing information when the system has insufficient evidence.

---

# 🔎 Query Engine

A separate lightweight query engine provides lower-level queries over current tracks, memory, and timeline.

Supported questions include:

```text
What objects do you see?
```

```text
What did you see earlier?
```

```text
What happened recently?
```

```text
When was the bottle last seen?
```

```text
Is the bottle visible?
```

```text
Where is the bottle?
```

The query interpreter is deterministic and uses predefined intent patterns rather than a general-purpose LLM.

---

# 🔁 Complete System Flow

A single frame can travel through the entire Aether architecture as follows:

```text
Camera
  │
  ▼
Frame
  │
  ▼
YOLOv8n
  │
  ▼
Detections
  │
  ▼
Confidence Filter
  │
  ▼
Tracker
  │
  ▼
Detection Stabilizer
  │
  ▼
Identity Resolver
  │
  ▼
Belief Engine
  │
  ▼
World Snapshot
  │
  ├───────────────► Scene Graph
  │
  ▼
Event Engine
  │
  ▼
Event Filter
  │
  ├───────────────► Working Memory
  │
  └───────────────► Timeline
                         │
                         ▼
                  Persistent Memory
                         │
                         ▼
                  Knowledge Engine
                         │
                  ┌──────┴──────┐
                  ▼             ▼
             Reasoning       Queries
                  │
                  ▼
               Planner
                  │
                  ▼
              Assistant
```

---

# 🧪 Evaluation Framework

Aether includes a dedicated evaluation framework rather than relying only on visual inspection.

The evaluator currently contains scenarios for:

* Identity stability
* Belief stability
* Event quality
* Reasoning accuracy
* Planner quality
* Query accuracy

The evaluation framework provides reusable metric primitives including:

* Percentage
* Counter
* Average
* Normalized Score

Example evaluation structure:

```text
Scenario
   ↓
Expected Result
   ↓
Actual Result
   ↓
Metric Calculation
   ↓
Evaluation Report
```

Run the evaluation suite with:

```bash
python -m evaluation
```

For Markdown output:

```bash
python -m evaluation --markdown
```

---

# 📊 Performance Monitoring

The perception pipeline measures frame processing performance and maintains a rolling frame-duration history.

The renderer displays the current FPS.

This allows the system to monitor real-time perception performance while the camera pipeline is running.

---

# 🛠️ Tech Stack

### Computer Vision

* Python
* OpenCV
* YOLOv8
* Ultralytics

### Numerical Computing

* NumPy

### Architecture

* Modular Python packages
* Dataclasses
* Type hints
* Protocol-based interfaces
* Deterministic rule engines

### Storage

* JSON persistence
* In-memory stores

### Testing

* Pytest
* Scenario-based evaluation

---

# 📂 Project Structure

```text
Aether-Vision/
│
├── app/
│   ├── main.py
│   └── runner.py
│
├── assistant/
│   ├── assistant.py
│   ├── exceptions.py
│   ├── formatter.py
│   ├── intent.py
│   ├── query.py
│   ├── query_engine.py
│   ├── query_handler.py
│   ├── response.py
│   └── response_builder.py
│
├── belief/
│   ├── belief.py
│   ├── belief_engine.py
│   ├── belief_policy.py
│   ├── belief_state.py
│   ├── exceptions.py
│   └── queries.py
│
├── camera/
│   ├── camera.py
│   ├── camera_manager.py
│   ├── exceptions.py
│   └── frame.py
│
├── data/
│   └── aether_memory.json
│
├── evaluation/
│   ├── benchmark.py
│   ├── evaluator.py
│   ├── metrics.py
│   ├── perf.py
│   ├── report.py
│   └── scenarios/
│       ├── belief_stability.py
│       ├── event_quality.py
│       ├── identity_stability.py
│       ├── planner_quality.py
│       ├── query_accuracy.py
│       └── reasoning_accuracy.py
│
├── events/
│   ├── event.py
│   ├── event_engine.py
│   ├── event_filter.py
│   ├── event_policy.py
│   ├── event_types.py
│   └── exceptions.py
│
├── identity/
│   ├── confidence_fusion.py
│   ├── identity.py
│   ├── label_history.py
│   ├── queries.py
│   └── resolver.py
│
├── knowledge/
│   ├── knowledge_engine.py
│   ├── knowledge_query.py
│   ├── knowledge_result.py
│   └── query_types.py
│
├── memory/
│   ├── constants.py
│   ├── enums.py
│   ├── memory_engine.py
│   ├── memory_record.py
│   ├── memory_store.py
│   ├── object_memory.py
│   ├── queries.py
│   └── schemas.py
│
├── pipeline/
│   ├── perception_pipeline.py
│   └── pipeline_result.py
│
├── planning/
│   ├── action.py
│   ├── goal.py
│   ├── plan.py
│   ├── planner.py
│   └── planner_rules.py
│
├── reasoning/
│   ├── inference.py
│   ├── inference_result.py
│   ├── query.py
│   ├── reasoning_engine.py
│   ├── rule.py
│   └── rule_registry.py
│
├── scene/
│   ├── graph.py
│   ├── graph_builder.py
│   ├── queries.py
│   ├── relation.py
│   └── relation_types.py
│
├── storage/
│   ├── memory_quality.py
│   ├── persistence.py
│   └── serializer.py
│
├── tests/
│   ├── test_belief_engine.py
│   ├── test_evaluation.py
│   ├── test_persistence.py
│   └── test_query_engine.py
│
├── timeline/
│   ├── timeline.py
│   ├── timeline_entry.py
│   ├── timeline_store.py
│   └── queries.py
│
├── tracking/
│   ├── association.py
│   ├── distance.py
│   ├── track.py
│   └── tracker.py
│
├── vision/
│   ├── adapters.py
│   ├── confidence_filter.py
│   ├── detection.py
│   ├── detection_stabilizer.py
│   ├── detector.py
│   ├── label_history.py
│   ├── model.py
│   ├── renderer.py
│   └── stabilization_policy.py
│
├── world/
│   ├── object_registry.py
│   ├── snapshot.py
│   └── world_state.py
│
├── requirements.txt
└── yolov8n.pt
```

---

# 🚀 Getting Started

## Prerequisites

Install:

* Python 3.10+
* OpenCV-compatible webcam
* Git
* A machine capable of running YOLOv8 inference

Recommended:

* NVIDIA GPU for improved real-time performance
* CUDA-enabled PyTorch installation when GPU acceleration is desired

---

# Installation

Clone the repository:

```bash
git clone <YOUR_REPOSITORY_URL>
cd Aether-Vision
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

### Windows

```powershell
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

The current dependency set includes:

```text
numpy
opencv-python
ultralytics
```

---

# ▶️ Running Aether

From the repository root:

```bash
python -m app.main
```

Aether will:

1. Open the configured camera
2. Capture frames
3. Run YOLO inference
4. Convert detections
5. Filter low-confidence detections
6. Track objects
7. Stabilize labels
8. Update identities and beliefs
9. Update world state
10. Generate spatial relationships
11. Detect events
12. Update memory and timeline
13. Render the current scene
14. Display FPS
15. Process supported assistant/query interactions

Press the configured quit key to stop the pipeline.

---

# 📷 Camera Configuration

The default camera source is:

```python
DEFAULT_CAMERA_INDEX = 0
```

This corresponds to the system's default webcam.

The camera abstraction also supports OpenCV-compatible sources.

For example:

```python
Camera(source=0)
```

can be replaced with another supported source.

---

# 🧠 Model Configuration

The default model is:

```text
yolov8n.pt
```

The detector uses lazy model loading and caches the loaded model.

The model path can be replaced through the `VisionDetector` constructor.

Example:

```python
VisionDetector(model_path="custom_model.pt")
```

---

# 🧪 Testing

Run the test suite with:

```bash
pytest
```

The repository includes tests covering areas such as:

* Belief engine
* Persistence
* Query engine
* Evaluation framework

---

# 📊 Evaluation

Run all benchmark scenarios:

```bash
python -m evaluation
```

Generate Markdown output:

```bash
python -m evaluation --markdown
```

Current evaluation categories:

```text
Identity Stability
Belief Stability
Event Quality
Reasoning Accuracy
Planner Quality
Query Accuracy
```

---

# 🔐 Persistence

Aether stores persistent memory in:

```text
data/aether_memory.json
```

The persistence layer performs atomic writes using a temporary file before replacing the target file.

If the persistence file is missing or invalid, Aether falls back to an empty memory state.

---

# ⚠️ Current Limitations

Aether is an experimental research/development system rather than a finished general-purpose artificial intelligence.

### Object Detection

YOLO predictions can be noisy.

Objects may occasionally be:

* Misclassified
* Missed
* Temporarily lost
* Assigned an incorrect label

Temporal stabilization reduces some of this noise but cannot eliminate detector errors.

### Tracking

The current tracker uses center-distance nearest-neighbour association.

This approach is intentionally simple and can struggle when:

* Objects overlap
* Objects cross paths
* Multiple similar objects are close together
* Objects move rapidly

### Spatial Understanding

Scene relationships are currently derived from 2D image geometry.

The system does not yet understand:

* True 3D distance
* Depth
* Physical containment
* Semantic object affordances
* Complex spatial relationships

### Reasoning

The reasoning layer is deterministic and rule-based.

It does not currently provide general-purpose commonsense reasoning.

### Planning

The planner generates explainable search actions but does not execute physical actions.

### Assistant

The assistant uses predefined deterministic query patterns rather than a general conversational language model.

### Memory

Persistent memory is currently JSON-based and designed for the project's experimental scale.

---

# 🗺️ Roadmap

### Perception

* [x] Camera abstraction
* [x] Frame abstraction
* [x] YOLO object detection
* [x] Confidence filtering
* [x] Detection normalization
* [x] FPS monitoring

### Tracking

* [x] Persistent track IDs
* [x] Nearest-neighbour association
* [x] Track history
* [x] Missed-frame handling
* [x] Detection stabilization

### World Model

* [x] World snapshots
* [x] Object registry
* [x] Scene graph
* [x] Spatial relations

### Memory

* [x] Working memory
* [x] Event-driven memory
* [x] Timeline
* [x] Persistent JSON memory
* [x] Memory confidence

### Cognition

* [x] Identity resolution
* [x] Belief engine
* [x] Knowledge engine
* [x] Rule-based reasoning
* [x] Deterministic planning
* [x] Query assistant

### Evaluation

* [x] Evaluation framework
* [x] Identity stability benchmark
* [x] Belief stability benchmark
* [x] Event quality benchmark
* [x] Reasoning benchmark
* [x] Planner benchmark
* [x] Query benchmark

### Future Development

* [ ] Stronger multi-object tracking
* [ ] Re-identification across longer disappearances
* [ ] Improved spatial reasoning
* [ ] Depth estimation
* [ ] 3D scene representation
* [ ] Object interaction modeling
* [ ] Temporal activity recognition
* [ ] Learned event detection
* [ ] More sophisticated reasoning
* [ ] LLM-assisted semantic reasoning
* [ ] Action execution
* [ ] Robotics integration
* [ ] Long-term episodic memory
* [ ] Multi-camera perception

---

# 🧱 Design Principles

Aether follows several architectural principles.

## 1. Separate perception from cognition

Computer vision produces observations.

Higher-level modules interpret those observations.

```text
Vision
  ↓
Observation
  ↓
World Model
  ↓
Knowledge
  ↓
Reasoning
  ↓
Planning
```

---

## 2. Preserve uncertainty

Aether does not immediately treat every detector prediction as absolute truth.

Confidence, history, belief stability, and temporal evidence are retained throughout the system.

---

## 3. Prefer deterministic reasoning

Core reasoning and planning are implemented using explicit rules.

This makes conclusions:

* Inspectable
* Testable
* Reproducible
* Easier to debug

---

## 4. Build around persistent entities

The system reasons about tracked objects rather than isolated bounding boxes.

```text
Detection
   ↓
Track
   ↓
Identity
   ↓
Belief
   ↓
Memory
```

---

## 5. Make information traceable

Knowledge results identify their source modules.

For example:

```text
WorkingMemory
CurrentObservation
PersistentMemory
Timeline
SceneGraph
BeliefEngine
```

This makes it possible to determine where an answer originated.

---

# 🔬 Why Aether Is Different From a Basic Object Detector

A conventional object detector performs:

```text
Frame → Objects
```

Aether attempts to perform:

```text
Frame
 ↓
Objects
 ↓
Persistent Identity
 ↓
World State
 ↓
Events
 ↓
Memory
 ↓
Relationships
 ↓
Beliefs
 ↓
Reasoning
 ↓
Plans
```

The goal is not simply to answer:

> "What is visible?"

but to build a continuously updated internal representation of:

> **What exists, what changed, what happened, what is known, what is uncertain, and what can be inferred from the accumulated evidence.**

---

# 🤝 Contributing

Contributions are welcome.

Create a feature branch:

```bash
git checkout -b feature/your-feature
```

Run tests:

```bash
pytest
```

Commit changes:

```bash
git add .
git commit -m "feat: add your feature"
```

Push the branch:

```bash
git push origin feature/your-feature
```

Then open a pull request.

---

# 📄 License

Add the project's chosen license here.

For example:

```text
MIT License
```

---

# 👨‍💻 Author

**Ayush Kottary**

Project Aether explores the intersection of:

```text
Computer Vision
       +
Object Tracking
       +
World Modeling
       +
Memory Systems
       +
Knowledge Representation
       +
Reasoning
       +
Planning
       +
AI Systems Engineering
```

---

# 📌 Project Status

**Experimental / Active Development**

Project Aether currently implements a functional layered perception pipeline with real-time camera input, YOLO-based object detection, object tracking, temporal label stabilization, identity resolution, belief management, world-state modeling, scene graphs, event detection, working and persistent memory, deterministic reasoning, planning, querying, and evaluation.

The architecture is intentionally modular so that more advanced perception, reasoning, memory, and robotics capabilities can be introduced incrementally.
