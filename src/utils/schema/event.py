import pandera as pa


def create_event_schema(
    coerce: bool = True, strict: bool = True, nullable: bool = False,
):
    """Function to validate that event schema is correct, it also does value checks in runtime
    (really nice stuff, right here). If this fails, then write to dead letter queue.

    Args:
        coerce (bool): Flag given to determine whether to coerce series to specified type
        strict (bool): Flag given to determine whether or not to accept columns in the
            dataframe that are not in the DataFrame
        nullable (bool): If columns should be nullable or not

    Returns: A pandas DataFrame schema that validates that the types are correct, and that the
    values inserted are correct.

    """
    return pa.DataFrameSchema(
        {
            "id": pa.Column(pa.String, nullable=nullable),
            "timestamp": pa.Column(pa.DateTime, nullable=nullable),
            "version": pa.Column(pa.String, nullable=nullable),
        },
        index=pa.Index(pa.Int),
        strict=strict,
        coerce=coerce,
    )
