"""
Modul 3: SessionManager & Epistemic Graph Store (Claim DAG)
Manages in-memory epistemic claim graphs, ClaimID allocation, and cascade invalidation algorithms.
"""

from typing import Dict, List, Set, Optional
from runtime.src.config import ClaimObject, EpistemicState, EvidenceLevel


class EpistemicGraphStore:
    def __init__(self):
        self.claims: Dict[str, ClaimObject] = {}
        self.counter: int = 0
        self.reverse_edges: Dict[str, Set[str]] = {}  # upstream_id -> set(downstream_ids)

    def generate_claim_id(self) -> str:
        self.counter += 1
        return f"CLM-{self.counter:06d}"

    def create_claim(
        self,
        statement: str,
        state: EpistemicState = EpistemicState.UNKNOWN,
        evidence_level: EvidenceLevel = EvidenceLevel.LEVEL_0_UNSUBSTANTIATED,
        depends_on: Optional[List[str]] = None,
    ) -> ClaimObject:
        claim_id = self.generate_claim_id()
        depends = depends_on or []

        # Cycle detection check
        for parent_id in depends:
            if self._has_path(parent_id, claim_id):
                raise ValueError(f"Circular dependency detected: {claim_id} -> {parent_id}")

        claim = ClaimObject(
            claim_id=claim_id,
            statement=statement,
            state=state,
            evidence_level=evidence_level,
            depends_on_claim_ids=depends,
        )
        self.claims[claim_id] = claim

        # Register reverse edges for cascade invalidation
        for parent_id in depends:
            if parent_id not in self.reverse_edges:
                self.reverse_edges[parent_id] = set()
            self.reverse_edges[parent_id].add(claim_id)

        return claim

    def _has_path(self, start_id: str, target_id: str) -> bool:
        if start_id == target_id:
            return True
        visited = set()
        stack = [start_id]
        while stack:
            curr = stack.pop()
            if curr == target_id:
                return True
            if curr not in visited:
                visited.add(curr)
                parent_claim = self.claims.get(curr)
                if parent_claim:
                    stack.extend(parent_claim.depends_on_claim_ids)
        return False

    def update_claim_state(self, claim_id: str, new_state: EpistemicState) -> List[str]:
        if claim_id not in self.claims:
            raise KeyError(f"Claim {claim_id} not found")

        claim = self.claims[claim_id]
        claim.state = new_state
        affected = [claim_id]

        # Trigger cascade invalidation if invalidated or suspect
        if new_state in (EpistemicState.INVALIDATED, EpistemicState.SUSPECT):
            affected.extend(self._cascade_suspect(claim_id))

        return affected

    def _cascade_suspect(self, upstream_id: str) -> List[str]:
        affected = []
        stack = list(self.reverse_edges.get(upstream_id, set()))
        visited = set()

        while stack:
            downstream_id = stack.pop()
            if downstream_id not in visited:
                visited.add(downstream_id)
                downstream_claim = self.claims.get(downstream_id)
                if downstream_claim and downstream_claim.state != EpistemicState.INVALIDATED:
                    downstream_claim.state = EpistemicState.SUSPECT
                    affected.append(downstream_id)
                    stack.extend(self.reverse_edges.get(downstream_id, set()))

        return affected

    def create_plugin_claim(
        self,
        plugin_id: str,
        statement: str,
        requested_state: EpistemicState = EpistemicState.HYPOTHESIS,
        evidence_level: EvidenceLevel = EvidenceLevel.LEVEL_0_UNSUBSTANTIATED,
        depends_on: Optional[List[str]] = None,
        evidence_refs: Optional[List[str]] = None,
    ) -> ClaimObject:
        """Enforces Truth Engine rule: Plugins CANNOT self-declare claims as VERIFIED_FACT
        without sufficient evidence (EvidenceLevel >= LEVEL_4_SPECIFICATION).
        """
        effective_state = requested_state
        if requested_state == EpistemicState.VERIFIED_FACT:
            if evidence_level.value < EvidenceLevel.LEVEL_4_SPECIFICATION.value:
                effective_state = EpistemicState.HYPOTHESIS

        refs = list(evidence_refs or [])
        refs.append(f"plugin:{plugin_id}")

        claim = self.create_claim(
            statement=statement,
            state=effective_state,
            evidence_level=evidence_level,
            depends_on=depends_on,
        )
        claim.evidence_refs = refs
        return claim

