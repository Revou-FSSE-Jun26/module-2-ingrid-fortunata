import pytest
from locustfile import CustomerJourneyTaskSet, CustomerUser, GradualRampLoadShape
from locust.shape import LoadTestShape


def test_locust_task_set_structure():
    """Verify that CustomerJourneyTaskSet contains all required sequential tasks."""
    tasks = CustomerJourneyTaskSet.tasks
    assert len(tasks) == 4

    # Verify method names corresponding to the 4 sequential user journey steps
    task_names = [t.__name__ for t in tasks]
    assert "get_all_products" in task_names
    assert "get_single_product" in task_names
    assert "post_new_order" in task_names
    assert "get_created_order" in task_names


def test_locust_user_configuration():
    """Verify CustomerUser configurations."""
    assert CustomerUser.tasks == [CustomerJourneyTaskSet]
    assert CustomerUser.wait_time is not None


def test_gradual_ramp_load_shape():
    """Verify GradualRampLoadShape computes user counts from 50 up to 200 users."""
    shape = GradualRampLoadShape()
    assert issubclass(GradualRampLoadShape, LoadTestShape)

    # Test stage progression
    # Stage 1: < 30s -> 50 users
    shape.get_run_time = lambda: 15
    user_count, spawn_rate = shape.tick()
    assert user_count == 50
    assert spawn_rate == 10

    # Stage 2: 30-90s -> 50 users
    shape.get_run_time = lambda: 60
    user_count, spawn_rate = shape.tick()
    assert user_count == 50

    # Stage 3/4: 90-180s -> 100 users
    shape.get_run_time = lambda: 150
    user_count, spawn_rate = shape.tick()
    assert user_count == 100

    # Stage 5/6: 180-300s -> 200 users
    shape.get_run_time = lambda: 250
    user_count, spawn_rate = shape.tick()
    assert user_count == 200

    # Beyond 300s -> completes (None)
    shape.get_run_time = lambda: 350
    assert shape.tick() is None
