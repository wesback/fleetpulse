// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toBeInTheDocument()
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Polyfill for TextEncoder/TextDecoder which is required by OpenTelemetry packages
import { TextEncoder, TextDecoder } from 'util';

global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;
