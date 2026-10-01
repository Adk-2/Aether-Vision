# Project Aether

### A Layered Computer Vision System for Perception, Memory, Reasoning, and World Understanding

Project Aether is an experimental **real-time visual perception and world-modeling system** designed to move beyond frame-by-frame object detection.

Instead of treating every camera frame as an isolated prediction, Aether maintains a continuously evolving representation of the observed world.

It combines:

- Object detection
- Object tracking
- Temporal label stabilization
- Identity resolution
- Belief management
- World-state modeling
- Spatial relationships
- Event detection
- Working memory
- Persistent memory
- Timeline construction
- Knowledge queries
- Deterministic reasoning
- Explainable planning
- Evaluation and benchmarking

The central idea is:

```text
Camera
  ↓
Perception
  ↓
Tracking
  ↓
Identity
  ↓
Belief
  ↓
World State
  ↓
Events + Memory
  ↓
Knowledge
  ↓
Reasoning
  ↓
Planning
  ↓
Assistant
```

---

# Overview

A conventional object detector primarily answers:

> What objects are visible in this frame?

Aether attempts to maintain answers to higher-level questions such as:

```text
What objects are currently visible?

Where was the object last observed?

What changed?

What happened to the object?

What objects are spatially related?

What does the system currently believe about an object?

What information has been observed previously?

What search action would make sense given the available evidence?
```

The system therefore treats visual understanding as a **continuous state-estimation problem**, rather than a sequence of independent detections.

---

# Core Architecture

```text
┌──────────────────────────────────────────────┐
│                    CAMERA                    │
│                OpenCV Capture                │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│                   VISION                     │
│                 YOLOv8n                      │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│                  TRACKING                    │
│          Persistent Track Association        │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│             IDENTITY + BELIEF                │
│     Label History • Confidence • Belief       │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│                WORLD STATE                   │
│            Current Object Registry            │
└───────────────┬──────────────┬───────────────┘
                ↓              ↓
         ┌────────────┐ ┌──────────────┐
         │   SCENE    │ │    EVENTS    │
         │   GRAPH    │ │    ENGINE    │
         └─────┬──────┘ └──────┬───────┘
               │               │
               └───────┬───────┘
                       ↓
               ┌──────────────┐
               │    MEMORY    │
               │  + TIMELINE  │
               └──────┬───────┘
                      ↓
               ┌──────────────┐
               │   KNOWLEDGE  │
               └──────┬───────┘
                      ↓
               ┌──────────────┐
               │   REASONING  │
               └──────┬───────┘
                      ↓
               ┌──────────────┐
               │   PLANNING   │
               └──────┬───────┘
                      ↓
               ┌──────────────┐
               │   ASSISTANT  │
               └──────────────┘
```

---

# Perception Pipeline

Each frame passes through a deterministic processing pipeline:

```text
Frame
 ↓
YOLOv8n Inference
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
Event Filter
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

The complete frame-processing cycle is orchestrated by `PerceptionPipeline`.

---

# Vision Layer

Aether currently uses:

```text
YOLOv8n
yolov8n.pt
```

The detector is isolated behind the `VisionDetector` abstraction so that the rest of the architecture does not directly depend on the detector implementation.

A detection contains information such as:

```text
class
confidence
bounding box
center
timestamp
```

---

# Confidence Filtering

Raw detector predictions are passed through a confidence filter before entering the downstream tracking pipeline.

Current production configuration:

```text
Confidence threshold: 0.35
```

Real-video evaluation demonstrated that some missed bottle instances were caused by low-confidence detections, while others were confidently classified as the wrong class.

---

# Object Tracking

Aether maintains persistent track IDs across frames.

The current tracker uses nearest-neighbour association based on object-center distance.

Current association threshold:

```text
50 pixels
```

Tracks maintain:

- Track ID
- Current detection
- Track history
- Missed frames
- Active/inactive state

---

# Temporal Detection Stabilization

Object detectors can produce frame-to-frame label fluctuations.

Aether maintains temporal label history and applies stabilization before changing the current stable label.

```text
Raw Predictions
      ↓
Label History
      ↓
Temporal Evidence
      ↓
Stable Label
```

---

# Identity Resolution

The identity layer associates semantic information with persistent tracks.

An identity can contain:

```text
Track ID
Current Label
Confidence
Label History
Last Update
```

The conceptual relationship is:

```text
Detection
   ↓
Track
   ↓
Identity
   ↓
Belief
```

---

# Belief Engine

Aether contains a separate belief layer for maintaining confidence in object identity.

Current policy includes:

```text
Minimum consecutive observations: 10
Minimum confidence margin:       0.20
Belief decay:                    0.98
Minimum belief confidence:       0.05
```

The system uses temporal evidence rather than immediately accepting every detector label change.

---

# World State

`WorldState` maintains the system's current representation of active objects.

```text
WorldSnapshot
 ├── timestamp
 └── active tracks
```

Previous and current snapshots are compared to determine what changed.

---

# Scene Graph

Aether constructs a lightweight spatial representation from tracked object geometry.

Current relationships include:

```text
LEFT_OF
RIGHT_OF
ABOVE
BELOW
NEAR
OVERLAPS
```

The scene graph is based on **2D image geometry**, not true 3D spatial understanding.

Current `NEAR` threshold:

```text
150 pixels
```

---

# Event Engine

The Event Engine compares world-state changes over time.

Events include:

```text
APPEARED
DISAPPEARED
MOVED
STOPPED
STARTED_MOVING
```

Events are derived from **temporal changes in world state**, rather than directly from individual detector predictions.

---

# Event Filtering

Raw perception can generate noisy movement events.

Aether therefore contains an event-filtering layer:

```text
Raw Perception Changes
          ↓
     Event Engine
          ↓
     Event Filter
          ↓
 Meaningful Events
```

Real-video evaluation demonstrated that event quality remains substantially more difficult than the deterministic synthetic scenarios.

---

# Memory

Events and object observations are converted into structured memory records.

Memory can retain:

```text
Object
Track ID
Status
Last Position
First Seen
Last Seen
Confidence
Historical Observations
```

---

# Timeline

Events are represented chronologically through the timeline layer.

Example:

```text
12:01:03  bottle_001 APPEARED
12:01:05  bottle_001 MOVED
12:01:08  bottle_001 STOPPED
12:01:12  bottle_001 DISAPPEARED
```

---

# Persistent Memory

Selected memory information can be persisted to:

```text
data/aether_memory.json
```

The persistence layer supports:

- Saving memory
- Loading memory
- Atomic writes
- Recovery from missing/invalid files
- Memory compaction

---

# Knowledge Engine

The Knowledge Engine provides a unified query layer over internal system state.

It combines:

```text
Current Observation
Working Memory
Persistent Memory
Timeline
Scene Graph
Belief Engine
```

Supported query concepts include:

```text
WHERE_IS
WHAT_HAPPENED
OBJECTS_NEAR
CURRENT_BELIEF
CURRENT_STATE
```

---

# Reasoning Engine

Aether includes a deterministic rule-based reasoning system.

```text
Known Facts
    ↓
Rule Evaluation
    ↓
New Conclusions
    ↓
Rule Evaluation
    ↓
Additional Conclusions
```

This makes reasoning:

- Inspectable
- Deterministic
- Testable
- Reproducible

The reasoning system is **not a general-purpose commonsense reasoning system**.

---

# Planning

The planner converts available knowledge and reasoning into explainable search actions.

Examples:

```text
Known location
    ↓
Inspect last known location
```

```text
Nearby evidence
    ↓
Search near related object
```

```text
Insufficient evidence
    ↓
Expand search area
```

The planner currently **proposes actions but does not physically execute them**.

---

# Aether Assistant

Aether exposes system knowledge through deterministic natural-language queries.

Examples:

```text
Where is the bottle?

Where was the bottle?

What happened to the bottle?

What is near the bottle?

How do I find the bottle?
```

The assistant combines:

```text
Knowledge
   +
Reasoning
   +
Planning
```

It is designed to avoid inventing information when the internal system lacks sufficient evidence.

---

# Evaluation Framework

Aether includes a dedicated evaluation framework rather than relying solely on visual inspection.

The evaluation system currently covers:

- Identity Stability
- Belief Stability
- Event Quality
- Reasoning Accuracy
- Planner Quality
- Query Accuracy
- Performance instrumentation
- Real-video evaluation

---

# Synthetic Evaluation

The latest deterministic evaluation suite:

```text
90 passed
6 subtests passed
16.25 seconds
```

### Identity Stability

```text
100% — 9000 / 9000
Cold-start mean: 1.325 frames
Adaptation:       31 frames
Burst tolerance:  20
```

### Belief Stability

```text
100% — 9000 / 9000
Cold-start mean: 10.375 frames
Adaptation:       43 frames
Burst tolerance:  20
```

### Event Quality

```text
100% — 34 / 34
Jitter false movement: 0 / 8
```

### Event Pipeline Quality

```text
100% — 8 / 8
Jitter false movement: 0 / 2
```

### Reasoning

```text
9 / 9 golden cases
```

### Planning

```text
6 / 6 golden cases
```

### Query Accuracy

```text
Supported queries:                40 / 40
Confidently wrong:                 0 / 40
Paraphrase handling:               0 / 60
Confidently wrong on paraphrases:  0 / 60
```

These results validate deterministic components under scripted conditions. They should **not** be interpreted as equivalent to general real-world vision performance.

---

# Real-World Evaluation

Aether was additionally evaluated against a manually annotated real-world video:

```text
Video:
data/evaluation/own_clips/desk_01.mp4

Resolution:
848 × 478

Source FPS:
30.004

Total frames:
2028

Annotated frames:
68
```

The evaluation used manually reviewed frames sampled throughout the clip.

The annotated evaluation focused on:

```text
bottle
wallet
phone
```

The ground-truth annotations were reviewed and corrected after a spatial mismatch was identified in the first 12 sampled frames.

---

# Real-World Baseline

Using the corrected annotations and production confidence threshold `0.35`:

```text
Detection precision: 33.33%
Detection recall:    14.84%

TP = 19
FP = 38
FN = 109
```

Identity evaluation:

```text
Spatially matched identity:
19 / 37 = 51.35%
```

Track ID switches:

```text
10
```

Filtered event evaluation:

```text
Event precision: 1.37%
Event recall:    27.27%

Event TP = 3
Event FP = 216
Event FN = 8
```

These real-video measurements are intentionally reported separately from the synthetic evaluation.

---

# Real-World Performance

Measured on the evaluated video:

```text
End-to-end mean FPS: 102.43
```

Excluding detector inference:

```text
1928.32 FPS
```

Representative stage latency:

| Stage | p50 | p95 |
|---|---:|---:|
| Detector | 8.410 ms | 14.663 ms |
| Adapter | 0.265 ms | 0.495 ms |
| Confidence Filter | 0.001 ms | 0.002 ms |
| Tracker | 0.013 ms | 0.023 ms |
| Stabilizer | 0.030 ms | 0.046 ms |
| Identity | 0.016 ms | 0.044 ms |
| Belief | 0.009 ms | 0.012 ms |
| World + Beliefs | 0.020 ms | 0.029 ms |
| Event Engine | 0.006 ms | 0.023 ms |
| Event Filter | 0.001 ms | 0.007 ms |

**YOLO inference dominates the measured end-to-end processing cost.**

---

# Real-World Diagnostic Findings

The real-video evaluation was followed by a diagnostic investigation rather than treating the aggregate score as the final explanation.

## 1. Ground-Truth Annotation Error

The first 12 sampled frames originally contained an incorrect bottle center.

The visible bottle was located substantially farther to the right than the annotated point.

The annotations were manually reviewed and corrected before the final evaluation.

This correction changed spatial matching for identity and event evaluation, but it did not create additional true-positive bottle detections at the production threshold.

---

## 2. Bottle Detection: Confidence vs Classification

For many of the originally mislabeled frames, YOLOv8n was not simply failing to detect the object.

It was detecting the object as:

```text
cup
```

with relatively high confidence.

Examples:

```text
Frame 30  → cup 0.5962
Frame 90  → cup 0.6224
Frame 120 → cup 0.6107
Frame 180 → cup 0.5254
Frame 240 → cup 0.4237
```

Therefore:

> Lowering the confidence threshold cannot fix these particular errors because the detector is confidently predicting the wrong class.

This is a **model/classification limitation**, rather than simply a confidence-filtering problem.

---

# Bottle Confidence Sweep

A bottle-only threshold sweep was performed on the corrected annotations.

| Threshold | TP | FP | FN | Precision | Recall |
|---:|---:|---:|---:|---:|---:|
| 0.35 | 19 | 0 | 49 | 100% | 27.94% |
| 0.32 | 27 | 0 | 41 | 100% | 39.71% |
| 0.30 | 32 | 0 | 36 | 100% | 47.06% |
| 0.28 | 38 | 0 | 30 | 100% | 55.88% |
| 0.25 | 41 | 0 | 27 | 100% | 60.29% |

### Important qualification

These are **bottle-only measurements from one controlled desk clip**.

They do not establish that lowering Aether's global production threshold will maintain zero false positives across arbitrary scenes or all detector classes.

The experiment provides evidence for further threshold investigation rather than a universal production-threshold recommendation.

---

# ID Switch Diagnosis

The real-video evaluation produced:

```text
10 track ID switches
```

The switches occurred after detector gaps that exceeded the tracker's configured missed-frame lifetime.

The investigation found that the switches were associated with **detection gaps followed by track expiration and subsequent track creation**, rather than an established nearest-neighbour association failure while the object remained continuously detected.

Therefore, no tracker-code modification was made as a result of this diagnostic phase.

```text
Detector gap
    ↓
Track timeout
    ↓
Old track becomes inactive
    ↓
Object detected again
    ↓
New track ID
```

---

# Wallet Out-of-Vocabulary Limitation

The real-video annotations included a `wallet` object.

However, `wallet` is not one of the classes available in the default YOLOv8n COCO model.

The model includes classes such as:

```text
bottle
cup
handbag
...
```

but not a literal:

```text
wallet
```

Therefore, literal wallet-class evaluation cannot be interpreted as a normal detector recall problem under the current model.

This is an **out-of-vocabulary limitation** of the selected pretrained detector.

A future custom detector or additional recognition layer would be required for reliable wallet-class recognition.

---

# What the Real-World Evaluation Taught

The real-video evaluation exposed several distinct failure modes:

```text
Annotation error
       ↓
Spatial matching discrepancy

Low-confidence bottle detections
       ↓
Potential threshold sensitivity

Bottle → cup classification
       ↓
Detector/model limitation

Detection gaps
       ↓
Track expiration
       ↓
New track IDs

Occlusion
       ↓
Reduced detector visibility

Wallet
       ↓
Out-of-vocabulary class
```

Each failure mode requires a different type of intervention.

---

# Current Limitations

Aether remains an experimental research/development system.

## Object Detection

YOLOv8n can:

- Miss objects
- Misclassify objects
- Produce low-confidence detections
- Produce inconsistent predictions under changing viewpoints
- Struggle with occlusion

Temporal stabilization can reduce some downstream instability, but it cannot correct a detector that consistently predicts the wrong class.

## Tracking

The current tracker uses center-distance nearest-neighbour association.

It can struggle when:

- Objects disappear for extended periods
- Objects overlap
- Objects cross paths
- Multiple similar objects are close together
- Detection quality becomes unstable

Longer detector gaps can cause tracks to expire and new IDs to be created.

## Object Vocabulary

The default YOLOv8n model is restricted to its pretrained class vocabulary.

Objects outside that vocabulary cannot be evaluated as literal detector classes without additional modeling.

## Spatial Understanding

The current scene representation is based on 2D image geometry.

Aether does not yet provide:

- True 3D distance
- Depth understanding
- Physical containment
- Full object affordances
- General physical reasoning

## Reasoning

The reasoning engine is deterministic and rule-based.

It is not a general-purpose commonsense reasoning system.

## Planning

The planner produces explainable actions but does not execute physical actions.

## Assistant

The current assistant uses deterministic query handling rather than a general-purpose conversational LLM.

## Memory

Persistent memory is currently JSON-based and intended for the experimental scale of the project.

---

# Evaluation Philosophy

Aether deliberately separates:

```text
Architecture Validation
```

from:

```text
Real-World Perception Validation
```

Synthetic evaluation asks:

> Does the architecture behave correctly under controlled conditions?

Real-video evaluation asks:

> What happens when the system encounters actual detector uncertainty, occlusion, classification errors, missed detections, and temporal gaps?

A high synthetic score is therefore not presented as evidence that the entire visual system has solved real-world perception.

---

# Design Principles

## 1. Separate Perception From Cognition

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

## 2. Preserve Uncertainty

Aether retains:

- Confidence
- Label history
- Belief state
- Temporal evidence

rather than immediately treating every detector prediction as absolute truth.

## 3. Prefer Deterministic Reasoning

Core reasoning and planning are implemented using explicit rules.

This makes their behavior:

- Inspectable
- Testable
- Reproducible
- Debuggable

## 4. Build Around Persistent Entities

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

## 5. Make Information Traceable

Knowledge results preserve their source information, making it possible to distinguish between:

```text
Current Observation
Working Memory
Persistent Memory
Timeline
Scene Graph
Belief
```

---

# Why Aether Is Different From a Basic Object Detector

A basic object detector performs:

```text
Frame
 ↓
Objects
```

Aether attempts to build:

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

The objective is therefore not simply:

> "What is visible?"

but:

> **What exists, what changed, what happened, what is known, what is uncertain, and what can be inferred from accumulated evidence?**

---

# Tech Stack

### Computer Vision

- Python
- OpenCV
- YOLOv8
- Ultralytics

### Numerical Computing

- NumPy

### Architecture

- Modular Python packages
- Dataclasses
- Type hints
- Protocol-based interfaces
- Deterministic rule engines

### Storage

- JSON persistence
- In-memory stores

### Testing

- Pytest
- Scenario-based evaluation
- Real-video evaluation
- Performance instrumentation

---

# Project Structure

```text
Aether-Vision/
│
├── app/
├── assistant/
├── belief/
├── camera/
├── data/
├── evaluation/
├── events/
├── identity/
├── knowledge/
├── memory/
├── pipeline/
├── planning/
├── reasoning/
├── scene/
├── storage/
├── tests/
├── timeline/
├── tracking/
├── vision/
├── world/
│
├── requirements.txt
└── yolov8n.pt
```

---

# Getting Started

## Prerequisites

- Python 3.10+
- OpenCV-compatible camera
- Git
- Machine capable of running YOLOv8 inference

An NVIDIA GPU can improve inference performance.

## Installation

```bash
git clone <YOUR_REPOSITORY_URL>
cd Aether-Vision
```

Create a virtual environment:

```bash
python -m venv .venv
```

### Windows

```powershell
.venv\Scriptsctivate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Running Aether

```bash
python -m app.main
```

The system then performs:

```text
Camera
 ↓
YOLO inference
 ↓
Detection normalization
 ↓
Confidence filtering
 ↓
Tracking
 ↓
Stabilization
 ↓
Identity
 ↓
Belief
 ↓
World state
 ↓
Events
 ↓
Memory
 ↓
Rendering
```

---

# Testing

Run the test suite:

```bash
pytest
```

Run the synthetic evaluation:

```bash
python -m evaluation
```

Generate Markdown evaluation output:

```bash
python -m evaluation --markdown
```

---

# Real-Video Evaluation

```bash
python -m evaluation.real_video_eval     --video data/evaluation/own_clips/desk_01.mp4     --labels data/evaluation/own_clips/desk_01_labels/labels.json
```

The real-video evaluation measures:

- Detection precision
- Detection recall
- Identity matching
- Track ID switches
- Event precision
- Event recall
- End-to-end FPS
- Stage-level latency

---

# Roadmap

## Perception

- [x] Camera abstraction
- [x] Frame abstraction
- [x] YOLO object detection
- [x] Detection normalization
- [x] Confidence filtering
- [x] FPS monitoring

## Tracking

- [x] Persistent track IDs
- [x] Nearest-neighbour association
- [x] Track history
- [x] Missed-frame handling
- [x] Temporal stabilization

## World Model

- [x] World snapshots
- [x] Object registry
- [x] Scene graph
- [x] Spatial relationships

## Memory

- [x] Working memory
- [x] Event-driven memory
- [x] Timeline
- [x] Persistent JSON memory
- [x] Memory confidence

## Cognition

- [x] Identity resolution
- [x] Belief engine
- [x] Knowledge engine
- [x] Rule-based reasoning
- [x] Deterministic planning
- [x] Query assistant

## Evaluation

- [x] Evaluation framework
- [x] Identity stability benchmark
- [x] Belief stability benchmark
- [x] Event benchmark
- [x] Reasoning benchmark
- [x] Planner benchmark
- [x] Query benchmark
- [x] Performance instrumentation
- [x] Real-video evaluation
- [x] Error diagnosis

## Future Development

- [ ] Stronger multi-object tracking
- [ ] Re-identification across longer disappearances
- [ ] Improved detector vocabulary
- [ ] Custom object detection training
- [ ] Improved spatial reasoning
- [ ] Depth estimation
- [ ] 3D scene representation
- [ ] Object interaction modeling
- [ ] Temporal activity recognition
- [ ] Learned event detection
- [ ] More sophisticated reasoning
- [ ] LLM-assisted semantic reasoning
- [ ] Physical action execution
- [ ] Robotics integration
- [ ] Long-term episodic memory
- [ ] Multi-camera perception

---

# Project Status

**Experimental / Active Development**

Project Aether currently implements a modular perception-to-reasoning pipeline combining real-time visual perception, tracking, identity, belief management, world-state modeling, spatial relationships, event processing, memory, deterministic reasoning, planning, querying, and evaluation.

The architecture has been validated under controlled synthetic scenarios and additionally tested against manually annotated real-world video.

The real-world evaluation shows that the current system is **not a solved general-purpose vision system**. Detector classification errors, missed detections, occlusion, out-of-vocabulary objects, and track expiration remain important limitations.

Rather than hiding these limitations behind aggregate scores, Aether's evaluation process attempts to identify the underlying cause of each failure and distinguish:

```text
Detector limitation
vs.
Threshold sensitivity
vs.
Tracking behavior
vs.
Annotation error
vs.
Out-of-vocabulary limitation
vs.
Downstream system behavior
```

This diagnostic approach is a core part of the project's engineering methodology.

---

# License

MIT License

---

# Author

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
