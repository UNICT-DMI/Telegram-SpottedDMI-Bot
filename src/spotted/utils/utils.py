from spotted.data import User


def get_user_by_id_or_index(user_id_or_idx: str, users_list: list[User]) -> User | None:
    """Get a user either by their user_id or by their index in a given list of users.
    The index is specified by prefixing the number with a '#' character.
    For example, '#0' would refer to the first user in the list.
    On the other hand, if the input is a number without the '#' prefix, it will be treated as a user_id.

    Args:
        user_id_or_idx: The user_id or index to look for.
            If it starts with '#', it will be treated as an index.
        users_list: The list of users to search through when looking for an index.

    Returns:
        The User object corresponding to the given user_id or index,
        or None if no such user exists.
    """
    if user_id_or_idx.startswith("#") and user_id_or_idx[1:].isdigit():
        idx = int(user_id_or_idx[1:])
        if 0 <= idx < len(users_list):
            return users_list[idx]
    elif user_id_or_idx.isdigit():
        return User(int(user_id_or_idx))
    return None
