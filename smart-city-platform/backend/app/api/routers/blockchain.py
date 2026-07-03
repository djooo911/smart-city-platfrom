"""
Blockchain explorer: list/paginate blocks, fetch one by index, verify
chain integrity, and filter events by device. All viewer+ (read-only).

Pagination for /blocks is done by slicing the full loaded chain rather
than a dedicated paginated query -- an academic-project chain stays small
enough that this is simpler than adding skip/limit to BlockchainRepository
for a listing that's already fully loaded for /verify anyway.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_blockchain_repository
from app.api.serializers import serialize_block
from app.domain.entities.enums import Role
from app.domain.interfaces.blockchain_repository import BlockchainRepository
from app.infrastructure.blockchain.chain import Blockchain
from app.security.rbac import CurrentUser, require_role

router = APIRouter(prefix="/blockchain", tags=["blockchain"])


@router.get("/blocks")
async def list_blocks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    blockchain_repository: BlockchainRepository = Depends(get_blockchain_repository),
    _current_user: CurrentUser = Depends(require_role(Role.VIEWER)),
) -> dict:
    blocks = await blockchain_repository.load_chain()
    start = (page - 1) * page_size
    page_blocks = blocks[start : start + page_size]

    return {
        "data": [serialize_block(block) for block in page_blocks],
        "meta": {"page": page, "page_size": page_size, "total_blocks": len(blocks)},
    }


@router.get("/blocks/{index}")
async def get_block(
    index: int,
    blockchain_repository: BlockchainRepository = Depends(get_blockchain_repository),
    _current_user: CurrentUser = Depends(require_role(Role.VIEWER)),
) -> dict:
    block = await blockchain_repository.get_block_by_index(index)
    if block is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Block not found")

    return {"data": serialize_block(block), "meta": {}}


@router.get("/verify")
async def verify_chain(
    blockchain_repository: BlockchainRepository = Depends(get_blockchain_repository),
    _current_user: CurrentUser = Depends(require_role(Role.VIEWER)),
) -> dict:
    blocks = await blockchain_repository.load_chain()
    if not blocks:
        return {"data": {"valid": True, "broken_at_index": None}, "meta": {"block_count": 0}}

    result = Blockchain(blocks=blocks).verify_chain()

    return {
        "data": {"valid": result.valid, "broken_at_index": result.broken_at_index},
        "meta": {"block_count": len(blocks)},
    }


@router.get("/events")
async def list_events(
    device_id: str = Query(...),
    blockchain_repository: BlockchainRepository = Depends(get_blockchain_repository),
    _current_user: CurrentUser = Depends(require_role(Role.VIEWER)),
) -> dict:
    blocks = await blockchain_repository.list_by_device(device_id)
    return {"data": [serialize_block(block) for block in blocks], "meta": {}}
