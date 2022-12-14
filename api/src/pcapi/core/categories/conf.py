from . import subcategories


CAN_CREATE_FROM_ISBN_SUBCATEGORIES = (subcategories.LIVRE_PAPIER.id,)


def can_create_from_isbn(subcategory_id: str | None) -> bool:
    return subcategory_id in CAN_CREATE_FROM_ISBN_SUBCATEGORIES
