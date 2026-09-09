import csv
import io
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from database import DbClient, get_db_client
from deps import require_user_id
from schemas import (
    ApiResponse,
    AvailabilityUpdate,
    CategoryCreate,
    CategoryUpdate,
    ModifierGroupCreate,
    ModifierGroupUpdate,
    ProductCreate,
    ProductUpdate,
    StockLimitUpdate,
)
from services import product_service
from services.business_service import CATALOG_READ_ROLES, assert_business_access

router = APIRouter(tags=["products"])


@router.get("/businesses/{business_id}/categories")
def list_categories(
    business_id: UUID,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    assert_business_access(client, business_id, user_id, CATALOG_READ_ROLES)
    return {"categories": product_service.list_categories(client, business_id)}


@router.post("/businesses/{business_id}/categories", response_model=ApiResponse)
def create_category(
    business_id: UUID,
    payload: CategoryCreate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    category = product_service.create_category(client, business_id, user_id, payload)
    return ApiResponse(message="Category created.", data=category)


@router.patch("/categories/{category_id}", response_model=ApiResponse)
def update_category(
    category_id: UUID,
    payload: CategoryUpdate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    category = product_service.update_category(client, category_id, user_id, payload)
    return ApiResponse(message="Category updated.", data=category)


@router.delete("/categories/{category_id}", response_model=ApiResponse)
def delete_category(
    category_id: UUID,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    product_service.delete_category(client, category_id, user_id)
    return ApiResponse(message="Category deleted.")


@router.get("/businesses/{business_id}/products/export")
def export_products_csv(
    business_id: UUID,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    assert_business_access(client, business_id, user_id, CATALOG_READ_ROLES)
    products = product_service.list_products(client, business_id, include_unavailable=True)
    categories = product_service.list_categories(client, business_id)
    cat_map = {str(c["id"]): c["name"] for c in categories}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "SKU", "Price", "Category ID", "Category Name", "Dietary", "Available", "Status"])
    for item in products:
        writer.writerow([
            item.get("name", ""),
            item.get("sku") or "",
            item.get("price", 0),
            item.get("category_id") or "",
            cat_map.get(str(item.get("category_id") or ""), ""),
            item.get("item_type", ""),
            "true" if item.get("is_available") else "false",
            item.get("menu_status") or "draft",
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="menu-items-{business_id}.csv"'},
    )


@router.get("/businesses/{business_id}/products")
def list_products(
    business_id: UUID,
    include_unavailable: bool = True,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    assert_business_access(client, business_id, user_id, CATALOG_READ_ROLES)
    return {
        "products": product_service.list_products(
            client, business_id, include_unavailable=include_unavailable
        )
    }


@router.post("/businesses/{business_id}/products", response_model=ApiResponse)
def create_product(
    business_id: UUID,
    payload: ProductCreate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    product = product_service.create_product(client, business_id, user_id, payload)
    return ApiResponse(message="Product created.", data=product)


@router.patch("/products/{product_id}", response_model=ApiResponse)
def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    product = product_service.update_product(client, product_id, user_id, payload)
    return ApiResponse(message="Product updated.", data=product)


@router.delete("/products/{product_id}", response_model=ApiResponse)
def delete_product(
    product_id: UUID,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    product_service.delete_product(client, product_id, user_id)
    return ApiResponse(message="Product deleted.")


@router.patch("/products/{product_id}/availability", response_model=ApiResponse)
def update_availability(
    product_id: UUID,
    payload: AvailabilityUpdate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    product = product_service.set_availability(
        client, product_id, user_id, payload.is_available
    )
    return ApiResponse(message="Availability updated.", data=product)


@router.patch("/products/{product_id}/stock-limit", response_model=ApiResponse)
def update_stock_limit(
    product_id: UUID,
    payload: StockLimitUpdate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    product = product_service.update_stock_limit(client, product_id, user_id, payload)
    return ApiResponse(message="Stock rules updated.", data=product)


@router.get("/products/{product_id}/modifier-groups")
def list_modifier_groups(
    product_id: UUID,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    return {
        "modifier_groups": product_service.list_modifier_groups(
            client,
            product_id,
            user_id,
        )
    }


@router.post("/products/{product_id}/modifier-groups", response_model=ApiResponse)
def create_modifier_group(
    product_id: UUID,
    payload: ModifierGroupCreate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    group = product_service.create_modifier_group(client, product_id, user_id, payload)
    return ApiResponse(message="Modifier group created.", data=group)


@router.patch("/modifier-groups/{group_id}", response_model=ApiResponse)
def update_modifier_group(
    group_id: UUID,
    payload: ModifierGroupUpdate,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    group = product_service.update_modifier_group(client, group_id, user_id, payload)
    return ApiResponse(message="Modifier group updated.", data=group)


@router.delete("/modifier-groups/{group_id}", response_model=ApiResponse)
def delete_modifier_group(
    group_id: UUID,
    user_id: UUID = Depends(require_user_id),
    client: DbClient = Depends(get_db_client),
):
    product_service.delete_modifier_group(client, group_id, user_id)
    return ApiResponse(message="Modifier group deleted.")
