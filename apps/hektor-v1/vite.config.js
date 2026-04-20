var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
import { execFile } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import nodemailer from 'nodemailer';
import { createClient } from '@supabase/supabase-js';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
function hektorDiffusionDevApi() {
    var projectRoot = fileURLToPath(new URL('../..', import.meta.url));
    var pythonPath = path.join(projectRoot, '.venv', 'Scripts', 'python.exe');
    var scriptPath = path.join(projectRoot, 'phase2', 'sync', 'hektor_diffusion_writeback.py');
    var refreshScriptPath = path.join(projectRoot, 'phase2', 'sync', 'refresh_single_annonce.py');
    var handleCommand = function (req, res, command) {
        if (req.method !== 'POST') {
            res.statusCode = 405;
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify({ error: 'Method not allowed' }));
            return;
        }
        var chunks = [];
        req.on('data', function (chunk) { return chunks.push(Buffer.from(chunk)); });
        req.on('end', function () {
            try {
                var raw = Buffer.concat(chunks).toString('utf-8') || '{}';
                var body_1 = JSON.parse(raw);
                var appDossierId = Number(body_1.appDossierId);
                if (!Number.isFinite(appDossierId) || appDossierId <= 0) {
                    res.statusCode = 400;
                    res.setHeader('Content-Type', 'application/json');
                    res.end(JSON.stringify({ error: 'Invalid appDossierId' }));
                    return;
                }
                var args = [scriptPath, command, '--app-dossier-id', String(appDossierId)];
                if (body_1.dryRun)
                    args.push('--dry-run');
                if (command === 'apply-targets' && body_1.ensureDiffusable)
                    args.push('--ensure-diffusable');
                execFile(pythonPath, args, { cwd: projectRoot, timeout: 120000 }, function (error, stdout, stderr) {
                    res.setHeader('Content-Type', 'application/json');
                    if (error) {
                        res.statusCode = 500;
                        res.end(JSON.stringify({
                            ok: false,
                            error: error.message,
                            stderr: stderr.trim() || null,
                            stdout: stdout.trim() || null,
                        }));
                        return;
                    }
                    try {
                        var payload_1 = JSON.parse(stdout);
                        var shouldRefreshSingleAnnonce = (command === 'accept-request' || command === 'apply-targets') &&
                            !body_1.dryRun &&
                            typeof (payload_1 === null || payload_1 === void 0 ? void 0 : payload_1.hektor_annonce_id) === 'string' &&
                            payload_1.hektor_annonce_id.trim().length > 0;
                        if (shouldRefreshSingleAnnonce) {
                            execFile(pythonPath, [refreshScriptPath, '--id-annonce', String(payload_1.hektor_annonce_id).trim()], { cwd: projectRoot, timeout: 120000 }, function (refreshError, refreshStdout, refreshStderr) {
                                if (refreshError) {
                                    res.statusCode = 200;
                                    res.end(JSON.stringify({
                                        ok: true,
                                        payload: __assign(__assign({}, payload_1), { refresh_single_annonce: {
                                                ok: false,
                                                error: refreshError.message,
                                                stdout: refreshStdout.trim() || null,
                                                stderr: refreshStderr.trim() || null,
                                            } }),
                                    }));
                                    return;
                                }
                                var refreshPayload = { stdout: refreshStdout.trim() || null, stderr: refreshStderr.trim() || null };
                                try {
                                    refreshPayload = JSON.parse(refreshStdout);
                                }
                                catch (_a) {
                                    // no-op
                                }
                                res.statusCode = 200;
                                res.end(JSON.stringify({
                                    ok: true,
                                    payload: __assign(__assign({}, payload_1), { refresh_single_annonce: refreshPayload }),
                                }));
                            });
                            return;
                        }
                        res.statusCode = 200;
                        res.end(JSON.stringify({ ok: true, payload: payload_1 }));
                    }
                    catch (_a) {
                        res.statusCode = 200;
                        res.end(JSON.stringify({ ok: true, payload: { stdout: stdout.trim() || null, stderr: stderr.trim() || null } }));
                    }
                });
            }
            catch (error) {
                res.statusCode = 500;
                res.setHeader('Content-Type', 'application/json');
                res.end(JSON.stringify({ ok: false, error: error instanceof Error ? error.message : 'Unexpected error' }));
            }
        });
    };
    var handleValidationCommand = function (req, res) {
        if (req.method !== 'POST') {
            res.statusCode = 405;
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify({ error: 'Method not allowed' }));
            return;
        }
        var chunks = [];
        req.on('data', function (chunk) { return chunks.push(Buffer.from(chunk)); });
        req.on('end', function () {
            try {
                var raw = Buffer.concat(chunks).toString('utf-8') || '{}';
                var body_2 = JSON.parse(raw);
                var appDossierId = Number(body_2.appDossierId);
                var state = Number(body_2.state);
                if (!Number.isFinite(appDossierId) || appDossierId <= 0 || ![0, 1].includes(state)) {
                    res.statusCode = 400;
                    res.setHeader('Content-Type', 'application/json');
                    res.end(JSON.stringify({ error: 'Invalid appDossierId or state' }));
                    return;
                }
                var args = [scriptPath, 'set-validation', '--app-dossier-id', String(appDossierId), '--state', String(state)];
                if (body_2.dryRun)
                    args.push('--dry-run');
                execFile(pythonPath, args, { cwd: projectRoot, timeout: 120000 }, function (error, stdout, stderr) {
                    res.setHeader('Content-Type', 'application/json');
                    if (error) {
                        res.statusCode = 500;
                        res.end(JSON.stringify({
                            ok: false,
                            error: error.message,
                            stderr: stderr.trim() || null,
                            stdout: stdout.trim() || null,
                        }));
                        return;
                    }
                    try {
                        var payload_2 = JSON.parse(stdout);
                        if (!body_2.dryRun && typeof (payload_2 === null || payload_2 === void 0 ? void 0 : payload_2.hektor_annonce_id) === 'string' && payload_2.hektor_annonce_id.trim().length > 0) {
                            execFile(pythonPath, [refreshScriptPath, '--id-annonce', String(payload_2.hektor_annonce_id).trim()], { cwd: projectRoot, timeout: 120000 }, function (refreshError, refreshStdout, refreshStderr) {
                                var refreshPayload = { stdout: refreshStdout.trim() || null, stderr: refreshStderr.trim() || null };
                                try {
                                    refreshPayload = JSON.parse(refreshStdout);
                                }
                                catch (_a) {
                                    // no-op
                                }
                                res.statusCode = 200;
                                res.end(JSON.stringify({
                                    ok: true,
                                    payload: __assign(__assign({}, payload_2), { refresh_single_annonce: refreshError
                                            ? {
                                                ok: false,
                                                error: refreshError.message,
                                                stdout: refreshStdout.trim() || null,
                                                stderr: refreshStderr.trim() || null,
                                            }
                                            : refreshPayload }),
                                }));
                            });
                            return;
                        }
                        res.statusCode = 200;
                        res.end(JSON.stringify({ ok: true, payload: payload_2 }));
                    }
                    catch (_a) {
                        res.statusCode = 200;
                        res.end(JSON.stringify({ ok: true, payload: { stdout: stdout.trim() || null, stderr: stderr.trim() || null } }));
                    }
                });
            }
            catch (error) {
                res.statusCode = 500;
                res.setHeader('Content-Type', 'application/json');
                res.end(JSON.stringify({ ok: false, error: error instanceof Error ? error.message : 'Unexpected error' }));
            }
        });
    };
    return {
        name: 'hektor-diffusion-dev-api',
        configureServer: function (server) {
            server.middlewares.use('/api/hektor-diffusion/targets', function (req, res) {
                var _a;
                if (req.method === 'GET') {
                    var url = new URL((_a = req.url) !== null && _a !== void 0 ? _a : '', 'http://localhost');
                    var appDossierId = Number(url.searchParams.get('appDossierId'));
                    if (!Number.isFinite(appDossierId) || appDossierId <= 0) {
                        res.statusCode = 400;
                        res.setHeader('Content-Type', 'application/json');
                        res.end(JSON.stringify({ error: 'Invalid appDossierId' }));
                        return;
                    }
                    execFile(pythonPath, [scriptPath, 'list-targets', '--app-dossier-id', String(appDossierId)], { cwd: projectRoot, timeout: 120000 }, function (error, stdout, stderr) {
                        res.setHeader('Content-Type', 'application/json');
                        if (error) {
                            res.statusCode = 500;
                            res.end(JSON.stringify({
                                ok: false,
                                error: error.message,
                                stderr: stderr.trim() || null,
                                stdout: stdout.trim() || null,
                            }));
                            return;
                        }
                        try {
                            res.statusCode = 200;
                            res.end(JSON.stringify({ ok: true, payload: JSON.parse(stdout) }));
                        }
                        catch (_a) {
                            res.statusCode = 200;
                            res.end(JSON.stringify({ ok: true, payload: { stdout: stdout.trim() || null, stderr: stderr.trim() || null } }));
                        }
                    });
                    return;
                }
                if (req.method !== 'POST') {
                    res.statusCode = 405;
                    res.setHeader('Content-Type', 'application/json');
                    res.end(JSON.stringify({ error: 'Method not allowed' }));
                    return;
                }
                var chunks = [];
                req.on('data', function (chunk) { return chunks.push(Buffer.from(chunk)); });
                req.on('end', function () {
                    var _a;
                    try {
                        var raw = Buffer.concat(chunks).toString('utf-8') || '{}';
                        var body = JSON.parse(raw);
                        var appDossierId = Number(body.appDossierId);
                        if (!Number.isFinite(appDossierId) || appDossierId <= 0) {
                            res.statusCode = 400;
                            res.setHeader('Content-Type', 'application/json');
                            res.end(JSON.stringify({ error: 'Invalid appDossierId' }));
                            return;
                        }
                        var payloadJson = JSON.stringify(Array.isArray(body.targets) ? body.targets : []);
                        var args = [
                            scriptPath,
                            'replace-targets',
                            '--app-dossier-id',
                            String(appDossierId),
                            '--requested-by',
                            String((_a = body.requestedBy) !== null && _a !== void 0 ? _a : 'app'),
                            '--payload-json',
                            payloadJson,
                        ];
                        execFile(pythonPath, args, { cwd: projectRoot, timeout: 120000 }, function (error, stdout, stderr) {
                            res.setHeader('Content-Type', 'application/json');
                            if (error) {
                                res.statusCode = 500;
                                res.end(JSON.stringify({
                                    ok: false,
                                    error: error.message,
                                    stderr: stderr.trim() || null,
                                    stdout: stdout.trim() || null,
                                }));
                                return;
                            }
                            try {
                                res.statusCode = 200;
                                res.end(JSON.stringify({ ok: true, payload: JSON.parse(stdout) }));
                            }
                            catch (_a) {
                                res.statusCode = 200;
                                res.end(JSON.stringify({ ok: true, payload: { stdout: stdout.trim() || null, stderr: stderr.trim() || null } }));
                            }
                        });
                    }
                    catch (error) {
                        res.statusCode = 500;
                        res.setHeader('Content-Type', 'application/json');
                        res.end(JSON.stringify({ ok: false, error: error instanceof Error ? error.message : 'Unexpected error' }));
                    }
                });
            });
            server.middlewares.use('/api/hektor-diffusion/seed', function (req, res) {
                if (req.method !== 'POST') {
                    res.statusCode = 405;
                    res.setHeader('Content-Type', 'application/json');
                    res.end(JSON.stringify({ error: 'Method not allowed' }));
                    return;
                }
                var chunks = [];
                req.on('data', function (chunk) { return chunks.push(Buffer.from(chunk)); });
                req.on('end', function () {
                    try {
                        var raw = Buffer.concat(chunks).toString('utf-8') || '{}';
                        var body = JSON.parse(raw);
                        var appDossierId = Number(body.appDossierId);
                        if (!Number.isFinite(appDossierId) || appDossierId <= 0) {
                            res.statusCode = 400;
                            res.setHeader('Content-Type', 'application/json');
                            res.end(JSON.stringify({ error: 'Invalid appDossierId' }));
                            return;
                        }
                        execFile(pythonPath, [scriptPath, 'seed-default-targets', '--app-dossier-id', String(appDossierId)], { cwd: projectRoot, timeout: 120000 }, function (error, stdout, stderr) {
                            res.setHeader('Content-Type', 'application/json');
                            if (error) {
                                res.statusCode = 500;
                                res.end(JSON.stringify({
                                    ok: false,
                                    error: error.message,
                                    stderr: stderr.trim() || null,
                                    stdout: stdout.trim() || null,
                                }));
                                return;
                            }
                            try {
                                res.statusCode = 200;
                                res.end(JSON.stringify({ ok: true, payload: JSON.parse(stdout) }));
                            }
                            catch (_a) {
                                res.statusCode = 200;
                                res.end(JSON.stringify({ ok: true, payload: { stdout: stdout.trim() || null, stderr: stderr.trim() || null } }));
                            }
                        });
                    }
                    catch (error) {
                        res.statusCode = 500;
                        res.setHeader('Content-Type', 'application/json');
                        res.end(JSON.stringify({ ok: false, error: error instanceof Error ? error.message : 'Unexpected error' }));
                    }
                });
            });
            server.middlewares.use('/api/hektor-diffusion/preview-targets', function (req, res) {
                var _a;
                if (req.method !== 'GET') {
                    res.statusCode = 405;
                    res.setHeader('Content-Type', 'application/json');
                    res.end(JSON.stringify({ error: 'Method not allowed' }));
                    return;
                }
                var url = new URL((_a = req.url) !== null && _a !== void 0 ? _a : '', 'http://localhost');
                var appDossierId = Number(url.searchParams.get('appDossierId'));
                if (!Number.isFinite(appDossierId) || appDossierId <= 0) {
                    res.statusCode = 400;
                    res.setHeader('Content-Type', 'application/json');
                    res.end(JSON.stringify({ error: 'Invalid appDossierId' }));
                    return;
                }
                execFile(pythonPath, [scriptPath, 'preview-default-targets', '--app-dossier-id', String(appDossierId)], { cwd: projectRoot, timeout: 120000 }, function (error, stdout, stderr) {
                    res.setHeader('Content-Type', 'application/json');
                    if (error) {
                        res.statusCode = 500;
                        res.end(JSON.stringify({
                            ok: false,
                            error: error.message,
                            stderr: stderr.trim() || null,
                            stdout: stdout.trim() || null,
                        }));
                        return;
                    }
                    try {
                        res.statusCode = 200;
                        res.end(JSON.stringify({ ok: true, payload: JSON.parse(stdout) }));
                    }
                    catch (_a) {
                        res.statusCode = 200;
                        res.end(JSON.stringify({ ok: true, payload: { stdout: stdout.trim() || null, stderr: stderr.trim() || null } }));
                    }
                });
            });
            server.middlewares.use('/api/hektor-diffusion/broadcasts', function (req, res) {
                var _a;
                if (req.method !== 'GET') {
                    res.statusCode = 405;
                    res.setHeader('Content-Type', 'application/json');
                    res.end(JSON.stringify({ error: 'Method not allowed' }));
                    return;
                }
                var url = new URL((_a = req.url) !== null && _a !== void 0 ? _a : '', 'http://localhost');
                var appDossierId = Number(url.searchParams.get('appDossierId'));
                if (!Number.isFinite(appDossierId) || appDossierId <= 0) {
                    res.statusCode = 400;
                    res.setHeader('Content-Type', 'application/json');
                    res.end(JSON.stringify({ error: 'Invalid appDossierId' }));
                    return;
                }
                execFile(pythonPath, [scriptPath, 'list-broadcasts', '--app-dossier-id', String(appDossierId)], { cwd: projectRoot, timeout: 120000 }, function (error, stdout, stderr) {
                    res.setHeader('Content-Type', 'application/json');
                    if (error) {
                        res.statusCode = 500;
                        res.end(JSON.stringify({
                            ok: false,
                            error: error.message,
                            stderr: stderr.trim() || null,
                            stdout: stdout.trim() || null,
                        }));
                        return;
                    }
                    try {
                        res.statusCode = 200;
                        res.end(JSON.stringify({ ok: true, payload: JSON.parse(stdout) }));
                    }
                    catch (_a) {
                        res.statusCode = 200;
                        res.end(JSON.stringify({ ok: true, payload: { stdout: stdout.trim() || null, stderr: stderr.trim() || null } }));
                    }
                });
            });
            server.middlewares.use('/api/hektor-diffusion/apply', function (req, res) {
                handleCommand(req, res, 'apply-targets');
            });
            server.middlewares.use('/api/hektor-diffusion/accept', function (req, res) {
                handleCommand(req, res, 'accept-request');
            });
            server.middlewares.use('/api/hektor-diffusion/set-validation', function (req, res) {
                handleValidationCommand(req, res);
            });
        },
    };
}
function diffusionNotificationDevApi(env) {
    var buildTransporter = function () {
        var _a, _b;
        var host = env.SMTP_HOST;
        var port = Number((_a = env.SMTP_PORT) !== null && _a !== void 0 ? _a : 587);
        var user = env.SMTP_USER;
        var pass = env.SMTP_PASS;
        var secure = String((_b = env.SMTP_SECURE) !== null && _b !== void 0 ? _b : '').trim().toLowerCase() === 'true' || port === 465;
        if (!host || !Number.isFinite(port) || !user || !pass) {
            throw new Error('SMTP non configure. Variables requises : SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS');
        }
        return nodemailer.createTransport({
            host: host,
            port: port,
            secure: secure,
            auth: { user: user, pass: pass },
        });
    };
    return {
        name: 'diffusion-notification-dev-api',
        configureServer: function (server) {
            var _this = this;
            server.middlewares.use('/api/notifications/diffusion-decision', function (req, res) {
                if (req.method !== 'POST') {
                    res.statusCode = 405;
                    res.setHeader('Content-Type', 'application/json');
                    res.end(JSON.stringify({ ok: false, error: 'Method not allowed' }));
                    return;
                }
                var chunks = [];
                req.on('data', function (chunk) { return chunks.push(Buffer.from(chunk)); });
                req.on('end', function () { return __awaiter(_this, void 0, void 0, function () {
                    var raw, body, to, subject, bodyText, transporter, smtpFrom, allowUserFrom, senderName, senderEmail, effectiveFrom, info, error_1;
                    var _a, _b, _c, _d, _e, _f, _g, _h, _j, _k, _l;
                    return __generator(this, function (_m) {
                        switch (_m.label) {
                            case 0:
                                _m.trys.push([0, 2, , 3]);
                                raw = Buffer.concat(chunks).toString('utf-8') || '{}';
                                body = JSON.parse(raw);
                                to = (_a = body.to) === null || _a === void 0 ? void 0 : _a.trim();
                                subject = (_b = body.subject) === null || _b === void 0 ? void 0 : _b.trim();
                                bodyText = (_c = body.bodyText) === null || _c === void 0 ? void 0 : _c.trim();
                                if (!to || !subject || !bodyText) {
                                    res.statusCode = 400;
                                    res.setHeader('Content-Type', 'application/json');
                                    res.end(JSON.stringify({ ok: false, error: 'Missing to, subject or bodyText' }));
                                    return [2 /*return*/];
                                }
                                transporter = buildTransporter();
                                smtpFrom = ((_d = env.SMTP_FROM) === null || _d === void 0 ? void 0 : _d.trim()) || ((_e = env.SMTP_USER) === null || _e === void 0 ? void 0 : _e.trim()) || '';
                                allowUserFrom = String((_f = env.SMTP_ALLOW_USER_FROM) !== null && _f !== void 0 ? _f : '').trim().toLowerCase() === 'true';
                                senderName = ((_g = body.fromName) === null || _g === void 0 ? void 0 : _g.trim()) || 'Application diffusion';
                                senderEmail = ((_h = body.fromEmail) === null || _h === void 0 ? void 0 : _h.trim()) || null;
                                effectiveFrom = allowUserFrom && senderEmail
                                    ? "\"".concat(senderName.replace(/"/g, "'"), "\" <").concat(senderEmail, ">")
                                    : smtpFrom
                                        ? "\"".concat(senderName.replace(/"/g, "'"), "\" <").concat(smtpFrom, ">")
                                        : null;
                                if (!effectiveFrom) {
                                    res.statusCode = 500;
                                    res.setHeader('Content-Type', 'application/json');
                                    res.end(JSON.stringify({ ok: false, error: 'SMTP_FROM ou SMTP_USER manquant pour definir l expediteur' }));
                                    return [2 /*return*/];
                                }
                                return [4 /*yield*/, transporter.sendMail({
                                        from: effectiveFrom,
                                        to: to,
                                        replyTo: ((_j = body.replyTo) === null || _j === void 0 ? void 0 : _j.trim()) || senderEmail || undefined,
                                        subject: subject,
                                        text: bodyText,
                                        html: ((_k = body.bodyHtml) === null || _k === void 0 ? void 0 : _k.trim()) || undefined,
                                    })];
                            case 1:
                                info = _m.sent();
                                res.statusCode = 200;
                                res.setHeader('Content-Type', 'application/json');
                                res.end(JSON.stringify({ ok: true, messageId: (_l = info.messageId) !== null && _l !== void 0 ? _l : null }));
                                return [3 /*break*/, 3];
                            case 2:
                                error_1 = _m.sent();
                                res.statusCode = 500;
                                res.setHeader('Content-Type', 'application/json');
                                res.end(JSON.stringify({ ok: false, error: error_1 instanceof Error ? error_1.message : 'Unexpected error' }));
                                return [3 /*break*/, 3];
                            case 3: return [2 /*return*/];
                        }
                    });
                }); });
            });
        },
    };
}
function adminUserDevApi(env) {
    var _a, _b;
    var supabaseUrl = (_a = env.VITE_SUPABASE_URL) === null || _a === void 0 ? void 0 : _a.trim();
    var serviceRoleKey = (_b = env.SUPABASE_SERVICE_ROLE_KEY) === null || _b === void 0 ? void 0 : _b.trim();
    var getAdminClient = function () {
        if (!supabaseUrl || !serviceRoleKey) {
            throw new Error('SUPABASE_SERVICE_ROLE_KEY non configure');
        }
        return createClient(supabaseUrl, serviceRoleKey, { auth: { persistSession: false, autoRefreshToken: false } });
    };
    return {
        name: 'admin-user-dev-api',
        configureServer: function (server) {
            var _this = this;
            server.middlewares.use('/api/admin/users/create', function (req, res) {
                if (req.method !== 'POST') {
                    res.statusCode = 405;
                    res.setHeader('Content-Type', 'application/json');
                    res.end(JSON.stringify({ ok: false, error: 'Method not allowed' }));
                    return;
                }
                var chunks = [];
                req.on('data', function (chunk) { return chunks.push(Buffer.from(chunk)); });
                req.on('end', function () { return __awaiter(_this, void 0, void 0, function () {
                    var raw, body, email, password, role, firstName, lastName, displayName, isActive, adminClient, created, userId, profileError, error_2;
                    var _a, _b, _c, _d, _e, _f, _g, _h;
                    return __generator(this, function (_j) {
                        switch (_j.label) {
                            case 0:
                                _j.trys.push([0, 3, , 4]);
                                raw = Buffer.concat(chunks).toString('utf-8') || '{}';
                                body = JSON.parse(raw);
                                email = (_a = body.email) === null || _a === void 0 ? void 0 : _a.trim().toLowerCase();
                                password = (_b = body.password) === null || _b === void 0 ? void 0 : _b.trim();
                                role = (_c = body.role) === null || _c === void 0 ? void 0 : _c.trim();
                                firstName = ((_d = body.firstName) === null || _d === void 0 ? void 0 : _d.trim()) || null;
                                lastName = ((_e = body.lastName) === null || _e === void 0 ? void 0 : _e.trim()) || null;
                                displayName = ((_f = body.displayName) === null || _f === void 0 ? void 0 : _f.trim()) || [firstName, lastName].filter(Boolean).join(' ') || email || null;
                                isActive = body.isActive !== false;
                                if (!email || !password || !role) {
                                    res.statusCode = 400;
                                    res.setHeader('Content-Type', 'application/json');
                                    res.end(JSON.stringify({ ok: false, error: 'Email, password and role are required' }));
                                    return [2 /*return*/];
                                }
                                adminClient = getAdminClient();
                                return [4 /*yield*/, adminClient.auth.admin.createUser({
                                        email: email,
                                        password: password,
                                        email_confirm: true,
                                        user_metadata: {
                                            first_name: firstName,
                                            last_name: lastName,
                                            display_name: displayName,
                                        },
                                    })];
                            case 1:
                                created = _j.sent();
                                if (created.error || !created.data.user) {
                                    throw new Error((_h = (_g = created.error) === null || _g === void 0 ? void 0 : _g.message) !== null && _h !== void 0 ? _h : 'Unable to create auth user');
                                }
                                userId = created.data.user.id;
                                return [4 /*yield*/, adminClient.from('app_user_profile').upsert({
                                        id: userId,
                                        email: email,
                                        role: role,
                                        first_name: firstName,
                                        last_name: lastName,
                                        display_name: displayName,
                                        is_active: isActive,
                                        updated_at: new Date().toISOString(),
                                    })];
                            case 2:
                                profileError = (_j.sent()).error;
                                if (profileError) {
                                    throw new Error(profileError.message);
                                }
                                res.statusCode = 200;
                                res.setHeader('Content-Type', 'application/json');
                                res.end(JSON.stringify({ ok: true, userId: userId, email: email }));
                                return [3 /*break*/, 4];
                            case 3:
                                error_2 = _j.sent();
                                res.statusCode = 500;
                                res.setHeader('Content-Type', 'application/json');
                                res.end(JSON.stringify({ ok: false, error: error_2 instanceof Error ? error_2.message : 'Unexpected error' }));
                                return [3 /*break*/, 4];
                            case 4: return [2 /*return*/];
                        }
                    });
                }); });
            });
            server.middlewares.use('/api/admin/users/list', function (_req, res) { return __awaiter(_this, void 0, void 0, function () {
                var adminClient, _a, data, error, error_3;
                return __generator(this, function (_b) {
                    switch (_b.label) {
                        case 0:
                            _b.trys.push([0, 2, , 3]);
                            adminClient = getAdminClient();
                            return [4 /*yield*/, adminClient
                                    .from('app_user_profile')
                                    .select('*')
                                    .order('is_active', { ascending: false })
                                    .order('display_name', { ascending: true })];
                        case 1:
                            _a = _b.sent(), data = _a.data, error = _a.error;
                            if (error)
                                throw new Error(error.message);
                            res.statusCode = 200;
                            res.setHeader('Content-Type', 'application/json');
                            res.end(JSON.stringify({ ok: true, users: data !== null && data !== void 0 ? data : [] }));
                            return [3 /*break*/, 3];
                        case 2:
                            error_3 = _b.sent();
                            res.statusCode = 500;
                            res.setHeader('Content-Type', 'application/json');
                            res.end(JSON.stringify({ ok: false, error: error_3 instanceof Error ? error_3.message : 'Unexpected error' }));
                            return [3 /*break*/, 3];
                        case 3: return [2 /*return*/];
                    }
                });
            }); });
            server.middlewares.use('/api/admin/users/update', function (req, res) {
                if (req.method !== 'POST') {
                    res.statusCode = 405;
                    res.setHeader('Content-Type', 'application/json');
                    res.end(JSON.stringify({ ok: false, error: 'Method not allowed' }));
                    return;
                }
                var chunks = [];
                req.on('data', function (chunk) { return chunks.push(Buffer.from(chunk)); });
                req.on('end', function () { return __awaiter(_this, void 0, void 0, function () {
                    var raw, body, id, email, role, adminClient, firstName, lastName, displayName, isActive, error, error_4;
                    var _a, _b, _c, _d, _e, _f;
                    return __generator(this, function (_g) {
                        switch (_g.label) {
                            case 0:
                                _g.trys.push([0, 2, , 3]);
                                raw = Buffer.concat(chunks).toString('utf-8') || '{}';
                                body = JSON.parse(raw);
                                id = (_a = body.id) === null || _a === void 0 ? void 0 : _a.trim();
                                email = (_b = body.email) === null || _b === void 0 ? void 0 : _b.trim().toLowerCase();
                                role = (_c = body.role) === null || _c === void 0 ? void 0 : _c.trim();
                                if (!id || !email || !role) {
                                    res.statusCode = 400;
                                    res.setHeader('Content-Type', 'application/json');
                                    res.end(JSON.stringify({ ok: false, error: 'id, email and role are required' }));
                                    return [2 /*return*/];
                                }
                                adminClient = getAdminClient();
                                firstName = ((_d = body.firstName) === null || _d === void 0 ? void 0 : _d.trim()) || null;
                                lastName = ((_e = body.lastName) === null || _e === void 0 ? void 0 : _e.trim()) || null;
                                displayName = ((_f = body.displayName) === null || _f === void 0 ? void 0 : _f.trim()) || [firstName, lastName].filter(Boolean).join(' ') || email;
                                isActive = body.isActive !== false;
                                return [4 /*yield*/, adminClient
                                        .from('app_user_profile')
                                        .update({
                                        email: email,
                                        role: role,
                                        first_name: firstName,
                                        last_name: lastName,
                                        display_name: displayName,
                                        is_active: isActive,
                                        updated_at: new Date().toISOString(),
                                    })
                                        .eq('id', id)];
                            case 1:
                                error = (_g.sent()).error;
                                if (error)
                                    throw new Error(error.message);
                                res.statusCode = 200;
                                res.setHeader('Content-Type', 'application/json');
                                res.end(JSON.stringify({ ok: true }));
                                return [3 /*break*/, 3];
                            case 2:
                                error_4 = _g.sent();
                                res.statusCode = 500;
                                res.setHeader('Content-Type', 'application/json');
                                res.end(JSON.stringify({ ok: false, error: error_4 instanceof Error ? error_4.message : 'Unexpected error' }));
                                return [3 /*break*/, 3];
                            case 3: return [2 /*return*/];
                        }
                    });
                }); });
            });
            server.middlewares.use('/api/admin/users/send-reset', function (req, res) {
                if (req.method !== 'POST') {
                    res.statusCode = 405;
                    res.setHeader('Content-Type', 'application/json');
                    res.end(JSON.stringify({ ok: false, error: 'Method not allowed' }));
                    return;
                }
                var chunks = [];
                req.on('data', function (chunk) { return chunks.push(Buffer.from(chunk)); });
                req.on('end', function () { return __awaiter(_this, void 0, void 0, function () {
                    var raw, body, email, adminClient, redirectTo, result, error_5;
                    var _a, _b;
                    return __generator(this, function (_c) {
                        switch (_c.label) {
                            case 0:
                                _c.trys.push([0, 2, , 3]);
                                raw = Buffer.concat(chunks).toString('utf-8') || '{}';
                                body = JSON.parse(raw);
                                email = (_a = body.email) === null || _a === void 0 ? void 0 : _a.trim().toLowerCase();
                                if (!email) {
                                    res.statusCode = 400;
                                    res.setHeader('Content-Type', 'application/json');
                                    res.end(JSON.stringify({ ok: false, error: 'email is required' }));
                                    return [2 /*return*/];
                                }
                                adminClient = getAdminClient();
                                redirectTo = (_b = env.APP_BASE_URL) === null || _b === void 0 ? void 0 : _b.trim();
                                return [4 /*yield*/, adminClient.auth.resetPasswordForEmail(email, redirectTo ? { redirectTo: redirectTo } : undefined)];
                            case 1:
                                result = _c.sent();
                                if (result.error)
                                    throw new Error(result.error.message);
                                res.statusCode = 200;
                                res.setHeader('Content-Type', 'application/json');
                                res.end(JSON.stringify({ ok: true }));
                                return [3 /*break*/, 3];
                            case 2:
                                error_5 = _c.sent();
                                res.statusCode = 500;
                                res.setHeader('Content-Type', 'application/json');
                                res.end(JSON.stringify({ ok: false, error: error_5 instanceof Error ? error_5.message : 'Unexpected error' }));
                                return [3 /*break*/, 3];
                            case 3: return [2 /*return*/];
                        }
                    });
                }); });
            });
        },
    };
}
export default defineConfig(function (_a) {
    var mode = _a.mode;
    var env = loadEnv(mode, process.cwd(), '');
    return {
        plugins: [react(), hektorDiffusionDevApi(), diffusionNotificationDevApi(env), adminUserDevApi(env)],
    };
});
