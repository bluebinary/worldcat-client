def get_exception_location(exception) -> tuple[str, int, str]:
    file: str = None
    line: int = None
    name: str = None

    if isinstance(exception, Exception):
        if hasattr(exception, "__traceback__"):
            traceback = exception.__traceback__

            while traceback:
                if tb_next := traceback.tb_next:
                    traceback = tb_next
                else:
                    break

            if frame := traceback.tb_frame:
                file = frame.f_code.co_filename
                line = frame.f_lineno
                name = (
                    frame.f_code.co_qualname
                    if hasattr(frame.f_code, "co_qualname")
                    else frame.f_code.co_name
                )

            del frame, traceback

    return (file, line, name)


def get_exception_locations(
    exception: Exception,
    all: bool = False,
) -> list[tuple[str, int, str]] | tuple[str, int, str]:
    locations: list[tuple[str, int, str]] = []

    def get_exception_location(traceback) -> tuple:
        file = line = name = None

        if frame := traceback.tb_frame:
            file = frame.f_code.co_filename
            line = frame.f_lineno
            name = (
                frame.f_code.co_qualname
                if hasattr(frame.f_code, "co_qualname")
                else frame.f_code.co_name
            )

        del frame, traceback

        return (file, line, name)

    if isinstance(exception, Exception):
        if hasattr(exception, "__traceback__"):
            traceback = exception.__traceback__

            if all is False:
                while _traceback := traceback.tb_next:
                    traceback = _traceback

            if location := get_exception_location(traceback):
                locations.append(location)

                if all is True:
                    while traceback := traceback.tb_next:
                        if location := get_exception_location(traceback):
                            locations.append(location)

            del traceback

    return locations if all else locations.pop() if locations else None
