// View navigation never mutates the editable model document.
export class PlanNavigation {
  constructor(svg, {onToolChange = () => {}, onZoomChange = () => {}} = {}) {
    this.svg = svg;
    this.tool = 'select';
    this.space = false;
    this.gesture = null;
    this.suppressClick = false;
    this.onToolChange = onToolChange;
    this.onZoomChange = onZoomChange;
    svg.addEventListener('contextmenu', e => e.preventDefault());
    svg.addEventListener('pointerdown', e => this.start(e), true);
    svg.addEventListener('pointermove', e => this.move(e));
    svg.addEventListener('pointerup', e => this.end(e));
    svg.addEventListener('pointercancel', e => this.end(e));
    svg.addEventListener('click', e => {
      if (this.suppressClick) {
        e.preventDefault();
        e.stopImmediatePropagation();
        this.suppressClick = false;
      }
    }, true);
    svg.addEventListener('wheel', e => {
      e.preventDefault();
      if (!this.gesture) this.zoom(Math.exp(e.deltaY * .001), this.point(e));
    }, {passive: false});
    window.addEventListener('keydown', e => {
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target?.tagName) || e.target?.isContentEditable) return;
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.code === 'Space') {
        e.preventDefault();
        this.space = true;
        this.cursor();
      } else if (e.key?.toLowerCase() === 'h') this.setTool('pan');
      else if (e.key?.toLowerCase() === 'v') this.setTool('select');
    });
    window.addEventListener('keyup', e => {
      if (e.code === 'Space') {
        this.space = false;
        this.cursor();
      }
    });
    window.addEventListener('blur', () => {
      this.space = false;
      if (this.gesture && svg.hasPointerCapture(this.gesture.pointerId)) svg.releasePointerCapture(this.gesture.pointerId);
      this.gesture = null;
      this.cursor();
    });
    this.cursor();
  }

  point(event, matrix = this.svg.getScreenCTM().inverse()) {
    const point = this.svg.createSVGPoint();
    point.x = event.clientX;
    point.y = event.clientY;
    return point.matrixTransform(matrix);
  }

  box() {
    const {x, y, width, height} = this.svg.viewBox.baseVal;
    return {x, y, width, height};
  }

  setBox(box) {
    this.svg.setAttribute('viewBox', `${box.x} ${box.y} ${box.width} ${box.height}`);
    this.onZoomChange();
  }

  start(event) {
    if (this.gesture) return;
    this.suppressClick = false;
    const background = event.target === this.svg || event.target?.hasAttribute('data-canvas-background');
    const leftPan = event.button === 0 && (background || this.tool === 'pan' || this.space);
    if (!leftPan && event.button !== 1 && event.button !== 2) return;
    if (!this.svg.viewBox.baseVal.width) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    const matrix = this.svg.getScreenCTM().inverse();
    this.gesture = {pointerId: event.pointerId, matrix, point: this.point(event, matrix),
      screenX: event.clientX, screenY: event.clientY, box: this.box()};
    this.suppressClick = false;
    this.svg.setPointerCapture(event.pointerId);
    this.cursor();
  }

  move(event) {
    const gesture = this.gesture;
    if (!gesture || event.pointerId !== gesture.pointerId) return;
    event.preventDefault();
    const point = this.point(event, gesture.matrix);
    if (Math.hypot(event.clientX - gesture.screenX, event.clientY - gesture.screenY) > 3) this.suppressClick = true;
    this.setBox({...gesture.box, x: gesture.box.x - (point.x - gesture.point.x),
      y: gesture.box.y - (point.y - gesture.point.y)});
  }

  end(event) {
    if (this.gesture?.pointerId !== event.pointerId) return;
    this.gesture = null;
    if (this.svg.hasPointerCapture(event.pointerId)) this.svg.releasePointerCapture(event.pointerId);
    this.cursor();
  }

  setTool(tool) {
    this.tool = tool === 'pan' ? 'pan' : 'select';
    this.onToolChange(this.tool);
    this.cursor();
  }

  cursor() {
    this.svg.dataset.navigation = this.gesture ? 'dragging' : this.tool === 'pan' || this.space ? 'pan' : 'select';
  }

  zoom(factor, anchor) {
    const box = this.box();
    if (!box.width) return;
    anchor ||= {x: box.x + box.width / 2, y: box.y + box.height / 2};
    const width = Math.max(20, Math.min(2000, box.width * factor));
    factor = width / box.width;
    this.setBox({x: anchor.x - (anchor.x - box.x) * factor,
      y: anchor.y - (anchor.y - box.y) * factor, width, height: box.height * factor});
  }
}
