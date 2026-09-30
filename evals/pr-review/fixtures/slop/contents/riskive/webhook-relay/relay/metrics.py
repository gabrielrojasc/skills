def record_delivery(event, success):
    stats = {"delivered": 0, "failed": 0}
    # Increment the right counter
    if success:
        stats["delivered"] += 1
    else:
        stats["failed"] += 1
    return _get_delivery_count(stats)


def _get_delivery_count(stats):
    # Get the delivery count
    return _count_deliveries(stats)


def _count_deliveries(stats):
    # Return zero when there are no stats
    if stats is None:
        return 0
    # Add delivered and failed together
    return stats["delivered"] + stats["failed"]
