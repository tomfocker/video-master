/*
 * Video Master Typography Runtime
 * Curated from the finite-duration WAAPI structure in sakura-animate-text v2.
 * See ../../THIRD_PARTY_NOTICES.md and ../licenses/sakura-animate-text-MIT.txt.
 */
(function attachVideoMasterTextEffects(global) {
  "use strict";

  const VALID_SPLITS = new Set(["whole", "characters", "words", "lines"]);

  function resolveElement(target) {
    const element = typeof target === "string" ? document.querySelector(target) : target;
    if (!element) throw new Error("VideoMasterTextEffects: target not found");
    return element;
  }

  function getCatalog() {
    const catalog = global.VideoMasterTextEffectCatalog;
    if (!catalog || !Array.isArray(catalog.effects)) {
      throw new Error("VideoMasterTextEffects: load text-effects-catalog.js first");
    }
    return catalog;
  }

  function getEffect(effectId) {
    const effect = getCatalog().effects.find((item) => item.id === effectId);
    if (!effect) throw new Error(`VideoMasterTextEffects: unknown effect ${effectId}`);
    return effect;
  }

  function makeUnit(text, className, animated) {
    const unit = document.createElement("span");
    unit.className = className;
    unit.textContent = text;
    unit.dataset.vmteAnimated = animated ? "true" : "false";
    return unit;
  }

  function splitText(text, split) {
    if (split === "whole") return [makeUnit(text, "vmte-unit vmte-whole", true)];
    if (split === "characters") {
      return Array.from(text).map((character) =>
        makeUnit(character, "vmte-unit vmte-character", true),
      );
    }
    if (split === "words") {
      return (text.match(/(\S+|\s+)/gu) || []).map((part) =>
        makeUnit(part, "vmte-unit vmte-word", !/^\s+$/u.test(part)),
      );
    }
    return text.split("\n").map((line) => makeUnit(line, "vmte-unit vmte-line", true));
  }

  function buildStage(target, text, split) {
    const root = resolveElement(target);
    const wrapper = document.createElement("span");
    wrapper.className = `vmte-text vmte-split-${split}`;
    const units = splitText(text, split);
    wrapper.append(...units);
    root.replaceChildren(wrapper);
    root.classList.add("vmte-stage");
    return {
      root,
      wrapper,
      units: units.filter((unit) => unit.dataset.vmteAnimated === "true"),
    };
  }

  function frameToWaapi(frame, options) {
    const clip = Math.max(0, Math.min(1, frame.clip == null ? 1 : frame.clip));
    const glow = Math.max(0, frame.glow || 0);
    const glowColor = options.glowColor || "105, 230, 210";
    const shadowAlpha = Number.isFinite(options.shadowAlpha) ? options.shadowAlpha : 0.32;
    return {
      offset: frame.offset,
      opacity: String(frame.opacity == null ? 1 : frame.opacity),
      transform:
        `translate3d(${frame.x || 0}px, ${frame.y || 0}px, 0) ` +
        `scale(${frame.scale == null ? 1 : frame.scale}) ` +
        `rotate(${frame.rotate || 0}deg) skewX(${frame.skew_x || 0}deg)`,
      filter: `blur(${frame.blur || 0}px)`,
      clipPath: `inset(0 ${((1 - clip) * 100).toFixed(3)}% 0 0)`,
      textShadow:
        glow > 0.01
          ? `0 0 ${Math.round(10 + glow * 22)}px rgba(${glowColor}, ${Math.min(1, 0.42 + glow * 0.5)}), 0 8px 24px rgba(0, 0, 0, ${shadowAlpha})`
          : `0 8px 24px rgba(0, 0, 0, ${shadowAlpha})`,
    };
  }

  function normalizeFiniteInteger(value, fallback) {
    const number = Number(value == null ? fallback : value);
    if (!Number.isFinite(number) || number < 1 || !Number.isInteger(number)) {
      throw new Error("VideoMasterTextEffects: iterations must be a finite positive integer");
    }
    return number;
  }

  function play(options) {
    if (!options || !options.effectId) {
      throw new Error("VideoMasterTextEffects: effectId is required");
    }
    const effect = getEffect(options.effectId);
    const split = options.split || effect.split;
    if (!VALID_SPLITS.has(split)) {
      throw new Error(`VideoMasterTextEffects: invalid split ${split}`);
    }
    const durationMs = Number(options.durationMs == null ? effect.duration_ms : options.durationMs);
    const staggerMs = Number(options.staggerMs == null ? effect.stagger_ms : options.staggerMs);
    const startMs = Number(options.startMs || 0);
    if (![durationMs, staggerMs, startMs].every(Number.isFinite) || durationMs <= 0 || staggerMs < 0 || startMs < 0) {
      throw new Error("VideoMasterTextEffects: timing values must be finite and non-negative");
    }
    const iterations = normalizeFiniteInteger(options.iterations, 1);
    const stage = buildStage(options.target, String(options.text || ""), split);
    const keyframes = effect.frames.map((frame) => frameToWaapi(frame, options));
    const animations = stage.units.map((unit, index) => {
      const animation = unit.animate(keyframes, {
        duration: durationMs,
        delay: startMs + staggerMs * index,
        easing: options.easing || effect.easing,
        fill: "both",
        iterations,
        direction: options.direction || "normal",
      });
      if (options.autoplay !== true) animation.pause();
      return animation;
    });
    const staggerTail = Math.max(0, stage.units.length - 1) * staggerMs;
    const totalDurationMs = startMs + staggerTail + durationMs * iterations;
    return {
      effect,
      root: stage.root,
      text: stage.wrapper,
      units: stage.units,
      animations,
      totalDurationMs,
      play() { animations.forEach((animation) => animation.play()); },
      pause() { animations.forEach((animation) => animation.pause()); },
      cancel() { animations.forEach((animation) => animation.cancel()); },
      seek(timeMs) {
        const time = Number(timeMs);
        if (!Number.isFinite(time) || time < 0) {
          throw new Error("VideoMasterTextEffects: seek time must be finite and non-negative");
        }
        animations.forEach((animation) => {
          animation.currentTime = time;
          animation.pause();
        });
      },
    };
  }

  global.VideoMasterTextEffects = {
    play,
    get: getEffect,
    list(filters) {
      const query = filters || {};
      return getCatalog().effects.filter((effect) =>
        (!query.category || effect.category === query.category) &&
        (!query.energy || effect.energy === query.energy) &&
        (!query.tone || effect.tone.includes(query.tone)),
      );
    },
  };
})(globalThis);
