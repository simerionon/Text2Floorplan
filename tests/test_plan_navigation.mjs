import assert from 'node:assert/strict';
import {test} from 'node:test';
import {PlanNavigation} from '../web_editor/static/plan_navigation.js';

function fixture(scale = 1) {
  const handlers = new Map(), keys = new Map(), captured = new Set();
  globalThis.window = {addEventListener: (name, fn) => keys.set(name, fn)};
  const svg = {
    dataset: {}, viewBox: {baseVal: {x: 0, y: 0, width: 100, height: 100}},
    addEventListener: (name, fn) => handlers.set(name, fn),
    getScreenCTM() { return {inverse: () => ({scale})}; },
    createSVGPoint() { return {x: 0, y: 0, matrixTransform(m) {return {x: this.x*m.scale, y: this.y*m.scale};}}; },
    setPointerCapture: id => captured.add(id),
    hasPointerCapture: id => captured.has(id),
    releasePointerCapture: id => captured.delete(id),
    setAttribute(name, value) {
      if (name === 'viewBox') {
        const [x, y, width, height] = value.split(/\s+/).map(Number);
        this.viewBox.baseVal = {x, y, width, height};
      }
    },
  };
  const navigation = new PlanNavigation(svg);
  const object = {hasAttribute: () => false};
  const event = (x, y, button = 0, target = svg) => ({
    clientX: x, clientY: y, button, pointerId: 1, target,
    preventDefault() {this.prevented = true;},
    stopImmediatePropagation() {this.stopped = true;},
  });
  const drag = (button = 0, target = svg) => {
    const start = event(10, 10, button, target);
    handlers.get('pointerdown')(start);
    handlers.get('pointermove')(event(40, 25, button, target));
    handlers.get('pointerup')(event(40, 25, button, target));
    return start;
  };
  return {svg, navigation, handlers, keys, captured, object, event, drag};
}

test('left drag on blank space pans without changing zoom', () => {
  const f = fixture(); f.drag();
  assert.deepEqual(f.svg.viewBox.baseVal, {x: -30, y: -15, width: 100, height: 100});
  assert.equal(f.captured.size, 0);
});
test('select mode leaves room and corner pointer events available', () => {
  const f = fixture(), start = f.drag(0, f.object);
  assert.equal(start.stopped, undefined);
  assert.equal(f.svg.viewBox.baseVal.x, 0);
});
test('hand tool pans over objects and intercepts their pointer handlers', () => {
  const f = fixture(); f.navigation.setTool('pan');
  assert.equal(f.drag(0, f.object).stopped, true);
  assert.equal(f.svg.viewBox.baseVal.x, -30);
});
test('Space temporarily enables panning, then restores select mode', () => {
  const f = fixture();
  f.keys.get('keydown')({code: 'Space', preventDefault() {}});
  f.drag(0, f.object);
  assert.equal(f.svg.viewBox.baseVal.x, -30);
  f.keys.get('keyup')({code: 'Space'});
  assert.equal(f.svg.dataset.navigation, 'select');
});
test('right and middle drag pan over objects', () => {
  for (const button of [1, 2]) {
    const f = fixture(); f.drag(button, f.object);
    assert.equal(f.svg.viewBox.baseVal.y, -15);
  }
});
test('panning uses the transform captured at gesture start', () => {
  const f = fixture(.5);
  f.handlers.get('pointerdown')(f.event(10, 10));
  f.svg.getScreenCTM = () => ({inverse: () => ({scale: 50})});
  f.handlers.get('pointermove')(f.event(40, 25));
  assert.equal(f.svg.viewBox.baseVal.x, -15);
  assert.equal(f.svg.viewBox.baseVal.y, -7.5);
});
test('cancelling a gesture releases capture', () => {
  const f = fixture();
  f.handlers.get('pointerdown')(f.event(10, 10));
  f.handlers.get('pointercancel')(f.event(10, 10));
  assert.equal(f.captured.size, 0);
  assert.equal(f.svg.dataset.navigation, 'select');
});
test('drag click is suppressed, but next normal object click is available', () => {
  const f = fixture(); f.drag();
  const dragClick = f.event(40, 25);
  f.handlers.get('click')(dragClick);
  assert.equal(dragClick.stopped, true);
  f.drag(2);
  f.handlers.get('pointerdown')(f.event(40, 25, 0, f.object));
  const click = f.event(40, 25, 0, f.object);
  f.handlers.get('click')(click);
  assert.equal(click.stopped, undefined);
});
test('zoom preserves its anchor and clamps extreme inputs', () => {
  const f = fixture();
  f.navigation.zoom(.5, {x: 20, y: 30});
  assert.deepEqual(f.svg.viewBox.baseVal, {x: 10, y: 15, width: 50, height: 50});
  f.navigation.zoom(.00001);
  assert.equal(f.svg.viewBox.baseVal.width, 20);
  f.navigation.zoom(100000);
  assert.equal(f.svg.viewBox.baseVal.width, 2000);
});
