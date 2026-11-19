import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import ts from 'typescript';

// Execute the real component's callbacks with deferred responses. This tests
// request ordering and navigation, not browser rendering or server authorization.
const source = readFileSync(process.env.LEARN_ENTRY_SOURCE ?? new URL('../pages/LearnEntry.tsx', import.meta.url), 'utf8');
const ast = ts.createSourceFile('LearnEntry.tsx', source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
const component = ast.statements.find(n => ts.isFunctionDeclaration(n) && n.name?.text === 'LearnEntry');
const names = ['setLearnerId', 'currentSelection', 'startSkillSession', 'startRecommended', 'startPlacement'];
const methods = component.body.statements.filter(n => ts.isFunctionDeclaration(n) && names.includes(n.name.text));
const load = component.body.statements.find(n => ts.isExpressionStatement(n) && ts.isCallExpression(n.expression)
  && n.expression.expression.getText(ast) === 'useEffect'
  && n.expression.arguments[1]?.getText(ast).includes('learnerId'));
const functions = methods.map(n => n.getText(ast)).join('\n');
const js = ts.transpileModule(`${functions}\nfunction installLoad() ${load.expression.arguments[0].body.getText(ast)}`, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None },
}).outputText;
const createScope = new Function('env', `with (env) { ${js}; return { installLoad, startRecommended, startSkillSession, startPlacement, select: typeof setLearnerId === 'function' ? setLearnerId : env.fallbackSelect }; }`);

function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
const flush = async () => { for (let i = 0; i < 8; i++) await Promise.resolve(); };
function harness() {
  const state = { id: '', skills: [], skillId: '', launchpad: null, loading: false, error: '' };
  const selection = { current: { id: '', version: 0 } };
  const requests = [], posts = [], navigation = [];
  const set = key => value => { state[key] = value; };
  const env = {
    selection, setSelectedLearnerId: set('id'), setSelectionVersion: () => {},
    setSkills: set('skills'), setSkillId: set('skillId'), setLaunchpad: set('launchpad'),
    setSkillsLoading: set('loading'), setError: set('error'),
    fallbackSelect: set('id'), navigate: path => navigation.push(path),
    ApiError: class extends Error {},
    api: url => { const d = deferred(); requests.push({ url, ...d }); return d.promise; },
    post: (url, body) => { const d = deferred(); posts.push({ url, body, ...d }); return d.promise; },
  };
  let cleanup;
  function render() {
    return createScope({ ...env, learnerId: state.id, launchpad: state.launchpad, skills: state.skills,
      selectedSkill: state.skills.find(s => s.id === state.skillId) });
  }
  function choose(id) {
    render().select(id);
    cleanup?.();
    cleanup = render().installLoad();
  }
  const request = (id, suffix, index = 0) => requests.filter(r => r.url === `/onboarding/learners/${id}/${suffix}`)[index];
  return { state, navigation, posts, choose, render, request, unmount: () => cleanup?.() };
}
const pad = id => ({ recommended: { id: `skill-${id}`, session_id: `session-${id}` } });

test('late prior-child launchpad cannot replace selected child or Resume session', async () => {
  const h = harness(); h.choose('A'); h.choose('B');
  h.request('B', 'launchpad').resolve(pad('B')); await flush();
  h.request('A', 'launchpad').resolve(pad('A')); await flush();
  await h.render().startRecommended();
  assert.equal(h.state.id, 'B');
  assert.deepEqual(h.navigation, ['/learn/session-B']);
});

test('old skills success and finally cannot overwrite current pending request', async () => {
  const h = harness(); h.choose('A'); h.choose('B');
  h.request('A', 'skills').resolve([{ id: 'skill-A' }]); await flush();
  assert.deepEqual(h.state.skills, []);
  assert.equal(h.state.loading, true);
  h.request('B', 'skills').resolve([{ id: 'skill-B' }]); await flush();
  assert.deepEqual(h.state.skills, [{ id: 'skill-B' }]);
  assert.equal(h.state.loading, false);
});

test('old failures cannot clear the current recommendation or show old errors', async () => {
  const h = harness(); h.choose('A'); h.choose('B');
  h.request('B', 'launchpad').resolve(pad('B')); await flush();
  h.request('A', 'launchpad').reject(new Error('old'));
  h.request('A', 'skills').reject(new Error('old')); await flush();
  assert.deepEqual(h.state.launchpad, pad('B'));
  assert.equal(h.state.error, '');
  assert.equal(h.state.loading, true);
});

test('A to B to A rejects first A response and keeps second A', async () => {
  const h = harness(); h.choose('A'); h.choose('B'); h.choose('A');
  h.request('A', 'launchpad', 1).resolve(pad('new-A')); await flush();
  h.request('A', 'launchpad', 0).resolve(pad('old-A')); await flush();
  assert.deepEqual(h.state.launchpad, pad('new-A'));
});

test('selection invalidates old controls immediately before effect cleanup', async () => {
  const h = harness(); h.choose('A');
  h.request('A', 'launchpad').resolve(pad('A')); await flush();
  const old = h.render(); old.select('B');
  await old.startRecommended();
  assert.deepEqual(h.navigation, []);
  assert.deepEqual(h.posts, []);
  assert.equal(h.state.launchpad, null);
});

test('unmounted requests cannot update state', async () => {
  const h = harness(); h.choose('A'); h.unmount();
  h.request('A', 'launchpad').resolve(pad('A'));
  h.request('A', 'skills').resolve([{ id: 'skill-A' }]); await flush();
  assert.equal(h.state.launchpad, null);
  assert.deepEqual(h.state.skills, []);
});

test('pending session start cannot navigate after child switch', async () => {
  const h = harness(); h.choose('A');
  const pending = h.render().startSkillSession('skill-A'); h.choose('B');
  h.posts[0].resolve({ session_id: 'new-session-A' }); await pending;
  assert.deepEqual(h.navigation, []);
});

test('pending placement cannot navigate after child switch', async () => {
  const h = harness(); h.choose('A');
  h.request('A', 'skills').resolve([{ id: 'skill-A', content_ready: true }]); await flush();
  const pending = h.render().startPlacement(); h.choose('B');
  h.posts[0].resolve({ session_id: 'diagnostic-A' }); await pending;
  assert.deepEqual(h.navigation, []);
});

test('current-child session and placement still navigate', async () => {
  const h = harness(); h.choose('B');
  h.request('B', 'skills').resolve([{ id: 'skill-B', content_ready: true }]); await flush();
  const start = h.render().startSkillSession('skill-B');
  h.posts[0].resolve({ session_id: 'new-session-B' }); await start;
  const placement = h.render().startPlacement();
  h.posts[1].resolve({ session_id: 'diagnostic-B' }); await placement;
  assert.deepEqual(h.navigation, ['/learn/new-session-B', '/diagnostic/diagnostic-B?learner=B']);
});
