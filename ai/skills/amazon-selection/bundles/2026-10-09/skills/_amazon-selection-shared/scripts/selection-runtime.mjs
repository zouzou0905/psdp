import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';

export const VERSION = 'selection-run-control-v1.1.0';
export const DIRECTIONS = ['evergreen', 'seasonal', 'holiday', 'trending', 'consumables', 'validated'];
export const BASELINE = {gates:'selection-gates-v0.10.0', market:'market-entry-v0.6.0', profit:'candidate-profit-workflow-v1.9.0', handoff:'batch-review-handoff-v2.0.0', execution:'selection-execution-v1.2.0', run:VERSION};
const SCOPES = ['type', 'market', 'target_configuration', 'prequote_economics', 'packaging', 'risk'];
const ACTIONS = new Set(['discover', 'verify_type', 'verify_market', 'verify_packaging', 'verify_cost', 'review', 'export', 'revalidate', 'repair_queue']);
const TYPES = new Set(['evergreen', 'seasonal', 'holiday', 'trending']);
const text = v => typeof v === 'string' && v.trim().length > 0;
const sameRules = (a, b) => b && Object.entries(a).every(([key, value]) => b[key] === value);

// This audits declared evidence receipts and lifecycle, not the truth of market data.
export function audit(state, now = new Date()) {
  if (state.schema_version !== 'selection-task-state-v1' || !text(state.task_id) || !['GB','DE','JP','CA'].includes(state.site)) throw Error('Invalid task identity/site/schema');
  if (!Number.isFinite(now.getTime())) throw Error('Invalid audit time');
  if (!Array.isArray(state.directions) || !state.directions.length || !state.rule_versions || !state.runtime) throw Error('Missing task contract');
  for (const key of ['gates','market','profit','handoff','execution','run']) if (!text(state.rule_versions[key])) throw Error(`Missing rule version: ${key}`);
  if (state.rule_versions.run !== VERSION) throw Error('Unsupported runtime contract');
  if (!sameRules(BASELINE, state.rule_versions)) throw Error('Task state does not use this release baseline; re-audit before counting');
  const directionKeys = new Set();
  for (const direction of state.directions) {
    if (!DIRECTIONS.includes(direction.key) || directionKeys.has(direction.key) || !Number.isInteger(direction.requested) || direction.requested < 1) throw Error('Invalid or duplicate direction/target');
    if (direction.key === 'validated' && direction.requested > 3) throw Error('Validated expansion cannot use a net-new 50-product target');
    directionKeys.add(direction.key);
  }
  const candidates = state.candidates ?? [];
  const ids = new Map(), opportunities = new Map();
  for (const row of candidates) {
    ids.set(row.candidate_id, (ids.get(row.candidate_id) ?? 0) + 1);
    if (row.active !== false) opportunities.set(row.opportunity_key, (opportunities.get(row.opportunity_key) ?? 0) + 1);
  }
  const eligible = [], excluded = [];
  for (const row of candidates) {
    const receipt = row.qualification_receipt;
    const errors = [];
    if (row.active === false) errors.push('withdrawn');
    if (!text(row.candidate_id) || ids.get(row.candidate_id) !== 1 || !text(row.opportunity_key) || opportunities.get(row.opportunity_key) !== 1) errors.push('duplicate_or_missing_identity');
    if (row.site !== state.site || !directionKeys.has(row.direction) || !TYPES.has(row.primary_type)) errors.push('site_direction_or_type_mismatch');
    const inquiryLane = row.inquiry_lane ?? 'strict';
    const requiredScopes = row.primary_type === 'evergreen' ? SCOPES : [...SCOPES, 'timing'];
    if (!receipt || receipt.decision !== 'quote_ready') errors.push('incomplete_qualification_receipt');
    if (inquiryLane === 'strict') {
      if (!requiredScopes.every(scope => receipt?.scopes?.[scope] === 'pass')) errors.push('incomplete_qualification_receipt');
    } else if (inquiryLane === 'controlled_test') {
      const reviewScopes = requiredScopes.filter(scope => receipt?.scopes?.[scope] === 'review');
      const gap = receipt?.controlled_evidence_gap_scope;
      const hardScopesPass = ['target_configuration','prequote_economics','packaging','risk'].every(scope => receipt?.scopes?.[scope] === 'pass');
      const everyOtherScopePass = requiredScopes.every(scope => scope === gap ? receipt?.scopes?.[scope] === 'review' : receipt?.scopes?.[scope] === 'pass');
      if (!['type','timing','market'].includes(gap) || reviewScopes.length !== 1 || reviewScopes[0] !== gap || !hardScopesPass || !everyOtherScopePass || receipt?.alternative_evidence_count < 2 || receipt?.human_review_required !== true) errors.push('controlled_test_receipt_invalid');
      if (row.direction === 'holiday' && gap === 'timing') errors.push('holiday_timing_controlled_test_disallowed');
      if (row.primary_type === 'trending' && ['type','timing'].includes(gap)) errors.push('trending_momentum_controlled_test_disallowed');
    } else errors.push('invalid_inquiry_lane');
    if (!sameRules(state.rule_versions, receipt?.rule_versions)) errors.push('rules_need_reaudit');
    if (!Array.isArray(receipt?.evidence_files) || !receipt.evidence_files.length || receipt.files_verified === false) errors.push('missing_or_changed_evidence_files');
    const evidenceAt = Date.parse(receipt?.source_as_of ?? '');
    const age = now.getTime() - evidenceAt;
    const ttl = row.primary_type === 'trending' ? 72 * 3600000 : 7 * 86400000;
    if (!Number.isFinite(age) || age < 0 || age > ttl) errors.push('data_stale_or_invalid_date');
    if (!['A','B','C'].includes(row.quote_priority)) errors.push('invalid_quote_priority');
    if (!['A','B','C'].includes(row.packaging_confidence)) errors.push('packaging_not_qualified');
    if (row.packaging_confidence === 'C' && row.quote_priority === 'A') errors.push('conservative_packaging_priority_required');
    if (errors.length) excluded.push({candidate_id: row.candidate_id ?? null, reasons: [...new Set(errors)]});
    else eligible.push(row);
  }
  const counts = state.directions.map(direction => {
    const rows = eligible.filter(row => row.direction === direction.key);
    const ordinary = rows.filter(row => row.quote_priority !== 'C' && (row.inquiry_lane ?? 'strict') === 'strict');
    const boundary = rows.filter(row => row.quote_priority === 'C' || (row.inquiry_lane ?? 'strict') === 'controlled_test');
    // Controlled-test and C-priority rows form one boundary union capped at 20%.
    const counted = [...ordinary, ...boundary.slice(0, Math.floor(ordinary.length / 4))];
    const delivery = direction.delivery;
    const deliveredIds = delivery?.candidate_ids;
    const countedById = new Map(counted.map(row => [row.candidate_id, row]));
    const uniqueDelivery = Array.isArray(deliveredIds) && new Set(deliveredIds).size === deliveredIds.length;
    const deliveredRows = uniqueDelivery ? deliveredIds.map(id => countedById.get(id)) : [];
    const matched = uniqueDelivery && deliveredRows.every(Boolean) && deliveredIds.length >= direction.requested;
    const boundaryCount = deliveredRows.filter(row => row?.quote_priority === 'C' || (row?.inquiry_lane ?? 'strict') === 'controlled_test').length;
    const ratioOkay = deliveredRows.length > 0 && boundaryCount / deliveredRows.length <= 0.2;
    const deliveryOkay = delivery?.qa_pass === true && delivery.files_verified !== false && sameRules(state.rule_versions, delivery.rule_versions) && text(delivery.path) && text(delivery.sha256) && matched && ratioOkay;
    return {direction: direction.key, requested: direction.requested, strict_quote_ready: counted.filter(row => (row.inquiry_lane ?? 'strict') === 'strict').length, controlled_test_quote: counted.filter(row => row.inquiry_lane === 'controlled_test').length, quote_ready: counted.length, gap: Math.max(0, direction.requested - counted.length), held_boundary: rows.length - counted.length, counted_ids: counted.map(row => row.candidate_id), completed: counted.length >= direction.requested && deliveryOkay};
  });
  const businessCompleted = counts.every(direction => direction.completed);
  const result = {runtime_contract: VERSION, task_id: state.task_id, business_status: businessCompleted ? 'completed' : 'incomplete', counts, excluded, execution_started: state.runtime.execution_authorized === true && state.runtime.native_goal_status === 'active'};
  const decision = (next, extras = {}) => ({...result, decision: next, ...extras});
  if (state.runtime.user_stop === true || state.runtime.native_goal_status === 'paused') return decision('stop_user');
  if (businessCompleted) return decision('complete');
  if (state.runtime.budget_available === false || state.runtime.native_goal_status === 'budget_limited') return decision('stop_budget');
  if (state.runtime.execution_authorized !== true || state.runtime.native_goal_status !== 'active') return decision('activation_required', {note: 'Configuration/checkpoint does not activate a persistent Goal.'});
  const incomplete = new Set(counts.filter(direction => !direction.completed).map(direction => direction.direction));
  const owned = (state.actions ?? []).filter(action => action.status === 'running' && incomplete.has(action.direction) && text(action.owner));
  const ready = (state.actions ?? []).filter(action => action.status === 'pending' && incomplete.has(action.direction) && !text(action.owner) && action.dependencies_ready === true && ACTIONS.has(action.kind));
  if (ready.length) {
    ready.sort((a,b) => (a.priority ?? 100) - (b.priority ?? 100));
    return decision('continue', {next_action: ready[0]});
  }
  if (owned.length) return decision('wait_owned_work', {owned_action_ids: owned.map(action => action.id)});
  if (counts.some(direction => direction.gap === 0 && !direction.completed)) return decision('repair_delivery');
  const proof = state.directions.filter(direction => incomplete.has(direction.key)).every(direction => direction.coverage_audit?.completed === true && direction.coverage_audit.files_verified !== false && direction.coverage_audit.alternatives_checked === true && direction.coverage_audit.source_files?.length > 0 && text(direction.coverage_audit.recovery_condition));
  if (!proof) return decision('repair_queue', {note: 'No pending action is not proof of market exhaustion. Audit coverage and register the next evidence-producing action.'});
  const blocker = state.blocking_audit;
  const turns = Array.isArray(blocker?.consecutive_goal_turn_ids) ? blocker.consecutive_goal_turn_ids : [];
  const persistent = text(blocker?.fingerprint) && blocker.same_condition === true && blocker.meaningful_progress === false && new Set(turns).size === turns.length && turns.length >= 3;
  return decision(persistent ? 'report_blocked' : 'audit_blocker', {recovery_conditions: state.directions.filter(direction => incomplete.has(direction.key)).map(direction => ({direction: direction.key, condition: direction.coverage_audit.recovery_condition}))});
}

export function verifyFiles(state, statePath) {
  const verify = ref => {
    try {
      if (!text(ref.path) || !/^[a-f0-9]{64}$/i.test(ref.sha256 ?? '')) return false;
      const file = path.resolve(path.dirname(statePath), ref.path);
      if (!fs.statSync(file).isFile()) return false;
      const digest = crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
      return digest.toLowerCase() === ref.sha256.toLowerCase();
    } catch { return false; }
  };
  const failures = [];
  for (const row of state.candidates ?? []) {
    if (row.active !== false && row.qualification_receipt) {
      const refs = row.qualification_receipt.evidence_files ?? [];
      row.qualification_receipt.files_verified = refs.length > 0 && refs.every(verify);
      if (!row.qualification_receipt.files_verified) failures.push({scope:'candidate', id:row.candidate_id});
    }
  }
  for (const direction of state.directions ?? []) {
    if (direction.delivery) {
      direction.delivery.files_verified = verify(direction.delivery);
      if (!direction.delivery.files_verified) failures.push({scope:'delivery', id:direction.key});
    }
    if (direction.coverage_audit) {
      const refs = direction.coverage_audit.source_files ?? [];
      direction.coverage_audit.files_verified = refs.length > 0 && refs.every(verify);
      if (!direction.coverage_audit.files_verified) failures.push({scope:'coverage', id:direction.key});
    }
  }
  return failures;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    if (process.argv[2] !== 'audit' || !process.argv[3]) throw Error('Usage: node selection-runtime.mjs audit <task-state.json> [ISO audit time]');
    const statePath = path.resolve(process.argv[3]);
    const state = JSON.parse(fs.readFileSync(statePath, 'utf8').replace(/^\uFEFF/, ''));
    const file_failures = verifyFiles(state, statePath);
    console.log(JSON.stringify({...audit(state, process.argv[4] ? new Date(process.argv[4]) : new Date()), file_failures}, null, 2));
  } catch (error) { console.error(JSON.stringify({status: 'invalid_state', error: error.message})); process.exitCode = 1; }
}
