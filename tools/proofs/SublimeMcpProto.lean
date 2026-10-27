/-
Model of the protocol-version routing in sublime_mcp.py (1.16.2):
  _mcp_dispatch (lines ~7324-7340), _mcp_dispatch_modern (~7343-7352),
  and the `initialize` echo rule in _mcp_dispatch_legacy (~7382-7386).
Only the routing decision is modelled; tool execution and JSON are not.
-/
namespace SublimeMcp

def modernVersions : List String := ["2026-07-28"]
def legacyVersions : List String := ["2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05"]
def newestLegacy : String := "2025-11-25"

/-- `requested if requested in _MCP_LEGACY_VERSIONS else _MCP_LEGACY_VERSIONS[0]` -/
def negotiate (requested : Option String) : String :=
  match requested with
  | some v => if v ∈ legacyVersions then v else newestLegacy
  | none => newestLegacy

/-- What the HTTP headers carry (absent on the legacy SSE transport). -/
structure Hdr where
  proto : Option String   -- MCP-Protocol-Version
  bodyOk : Bool           -- Mcp-Method (and Mcp-Name for tools/call) agree with the body

structure Req where
  hasId : Bool            -- msg_id is not None
  ver : Option String    -- params._meta["io.modelcontextprotocol/protocolVersion"]
  http : Option Hdr       -- none = headers is None

inductive Route
  | headerMissingMeta     -- 400, -32020: header says modern, _meta has no version
  | modernNotification    -- 202, no body
  | unsupported           -- 400, -32022
  | headerMismatch        -- 400, -32020
  | modernServe           -- handled as a modern request
  | legacy                -- handled by _mcp_dispatch_legacy
  deriving DecidableEq

def route (r : Req) : Route :=
  match r.ver with
  | none =>
    match r.http with
    | some h =>
      match h.proto with
      | some p => if p ∈ modernVersions then .headerMissingMeta else .legacy
      | none => .legacy
    | none => .legacy
  | some v =>
    if r.hasId = false then .modernNotification
    else if v ∉ modernVersions then .unsupported
    else
      match r.http with
      | none => .modernServe
      | some h => if h.proto = some v ∧ h.bodyOk = true then .modernServe else .headerMismatch

/-- (HTTP status, JSON-RPC error code) for the routes that decide it by themselves. -/
def verdict : Route → Option (Nat × Option Int)
  | .headerMissingMeta => some (400, some (-32020))
  | .modernNotification => some (202, none)
  | .unsupported => some (400, some (-32022))
  | .headerMismatch => some (400, some (-32020))
  | .modernServe => none
  | .legacy => none

/-! ### initialize -/

theorem newestLegacy_is_head : legacyVersions.head? = some newestLegacy := by decide

theorem negotiate_mem (r : Option String) : negotiate r ∈ legacyVersions := by
  cases r with
  | none => decide
  | some v =>
    by_cases h : v ∈ legacyVersions
    · simp [negotiate, h]
    · simp [negotiate, h]; decide

/-- A client that asks for a version the server lists gets exactly that version. -/
theorem negotiate_echo (v : String) (h : v ∈ legacyVersions) : negotiate (some v) = v := by
  simp [negotiate, h]

/-- Anything else (unknown version, or none) gets the newest legacy version. -/
theorem negotiate_fallback (v : String) (h : v ∉ legacyVersions) :
    negotiate (some v) = newestLegacy := by
  simp [negotiate, h]

/-- Negotiating twice changes nothing. -/
theorem negotiate_idem (r : Option String) : negotiate (some (negotiate r)) = negotiate r :=
  negotiate_echo _ (negotiate_mem r)

/-- A server never answers `initialize` with a modern version. -/
theorem negotiate_not_modern (r : Option String) : negotiate r ∉ modernVersions := by
  have h := negotiate_mem r
  revert h
  generalize negotiate r = x
  simp [legacyVersions, modernVersions]
  intro h; rcases h with h | h | h | h <;> simp [h]

/-- `_MCP_PROTOCOL_VERSIONS` lists no version twice. -/
theorem no_overlap : ∀ v ∈ modernVersions, v ∉ legacyVersions := by decide

/-! ### routing -/

/-- Every request carrying a version in `_meta` and an id, with a version the server does not
list as modern, is refused with 400 / -32022, whatever the headers say. -/
theorem unsupported_version (r : Req) (v : String) (hm : r.ver = some v) (hi : r.hasId = true)
    (hv : v ∉ modernVersions) : route r = .unsupported := by
  simp [route, hm, hi, hv]

/-- The consequence the 1.16.2 comment hints at: a *legacy* version in `_meta` is not served as
legacy; it gets -32022. -/
theorem legacy_version_in_meta_refused (r : Req) (hm : r.ver = some "2025-11-25")
    (hi : r.hasId = true) : verdict (route r) = some (400, some (-32022)) := by
  simp [route, hm, hi, modernVersions, verdict]

/-- A request without a version in `_meta` is never served as modern. -/
theorem no_meta_never_modern (r : Req) (hm : r.ver = none) :
    route r = .legacy ∨ route r = .headerMissingMeta := by
  unfold route
  rw [hm]
  simp only []
  cases r.http with
  | none => simp
  | some h =>
    cases hp : h.proto with
    | none => simp [hp]
    | some p => by_cases hq : p ∈ modernVersions <;> simp [hp, hq]

/-- A request served as modern over HTTP had a protocol header equal to its `_meta` version. -/
theorem modern_serve_header_agrees (r : Req) (v : String) (hm : r.ver = some v)
    (hs : route r = .modernServe) (h : Hdr) (hh : r.http = some h) : h.proto = some v := by
  unfold route at hs
  rw [hm, hh] at hs
  simp only [] at hs
  by_cases hi : r.hasId = false
  · simp [hi] at hs
  · by_cases hv : v ∉ modernVersions
    · simp [hi, hv] at hs
    · by_cases hc : h.proto = some v ∧ h.bodyOk = true
      · exact hc.1
      · simp [hi, hv, hc] at hs

/-- A modern notification is never answered with an error. -/
theorem notification_no_error (r : Req) (v : String) (hm : r.ver = some v)
    (hi : r.hasId = false) : verdict (route r) = some (202, none) := by
  simp [route, hm, hi, verdict]

/-- Routing is deterministic on exactly the fields it reads (a sanity check on the model). -/
theorem route_ext (a b : Req) (h1 : a.hasId = b.hasId) (h2 : a.ver = b.ver)
    (h3 : a.http = b.http) : route a = route b := by
  simp [route, h1, h2, h3]

end SublimeMcp
