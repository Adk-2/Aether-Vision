"""Application bootstrap for the perception pipeline."""

from pipeline import PerceptionPipeline


def run(pipeline: PerceptionPipeline | None = None) -> None:
    """Run perception cycles until the pipeline requests shutdown."""
    perception_pipeline = pipeline or PerceptionPipeline()
    try:
        perception_pipeline.start()
        while True:
            result = perception_pipeline.process_next_frame()
            if result.should_quit:
                break
    except KeyboardInterrupt:
        pass
    finally:
        perception_pipeline.close()
