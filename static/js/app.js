/**
 * TicketFlow — Portfolio UI (vanilla JS)
 * All writes use existing /api/* endpoints. INR formatting throughout.
 */
const TicketApp = (function () {
  'use strict';

  const API = '/api';
  let cachedBookingLookup = null;

  function $(id) { return document.getElementById(id); }
  function show(el) { if (el) el.classList.remove('hidden'); }
  function hide(el) { if (el) el.classList.add('hidden'); }

  function escapeHtml(str) {
    const d = document.createElement('div');
    d.textContent = str == null ? '' : String(str);
    return d.innerHTML;
  }

  function formatINR(amount) {
    const n = Math.round(Number(amount) || 0);
    return '₹' + n.toLocaleString('en-IN');
  }

  function formatDate(iso) {
    if (!iso) return '—';
    try {
      return new Date(iso).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
    } catch (e) {
      return iso;
    }
  }

  function getQueryParam(name) {
    return new URLSearchParams(window.location.search).get(name);
  }

  function showToast(message, type) {
    const c = $('toastContainer');
    if (!c) return;
    const t = document.createElement('div');
    t.className = 'toast toast-' + (type || 'info');
    t.textContent = message;
    c.appendChild(t);
    setTimeout(function () { t.remove(); }, 4500);
  }

  function showGlobalLoading(on) {
    const el = $('globalLoading');
    if (!el) return;
    if (on) {
      el.classList.remove('hidden');
      el.setAttribute('aria-hidden', 'false');
    } else {
      el.classList.add('hidden');
      el.setAttribute('aria-hidden', 'true');
    }
  }

  async function apiRequest(method, path, body) {
    const opts = { method: method, headers: { Accept: 'application/json' } };
    if (body !== undefined) {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(API + path, opts);
    let data = null;
    if ((res.headers.get('content-type') || '').includes('application/json')) {
      data = await res.json();
    }
    return { ok: res.ok, status: res.status, data: data };
  }

  async function fetchUiBooking(bookingId) {
    const res = await fetch('/api/ui/booking/' + bookingId, {
      headers: { Accept: 'application/json' },
    });
    let data = null;
    if ((res.headers.get('content-type') || '').includes('application/json')) {
      data = await res.json();
    }
    return { ok: res.ok, status: res.status, data: data };
  }

  async function checkHealth() {
    const badge = $('healthStatus');
    if (!badge) return;
    try {
      const res = await fetch('/health');
      const data = await res.json();
      if (res.ok && data.status === 'healthy') {
        badge.textContent = 'API Online';
        badge.className = 'health-badge health-ok';
      } else throw new Error();
    } catch (e) {
      badge.textContent = 'API Offline';
      badge.className = 'health-badge health-error';
    }
  }

  function initNavToggle() {
    const toggle = $('navToggle');
    const nav = $('mainNav');
    if (!toggle || !nav) return;

    function setNavOpen(open) {
      nav.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      document.body.classList.toggle('nav-open', open);
    }

    nav.querySelectorAll('.nav-link').forEach(function (link) {
      link.addEventListener('click', function () {
        setNavOpen(false);
      });
    });

    toggle.addEventListener('click', function (e) {
      e.stopPropagation();
      setNavOpen(!nav.classList.contains('open'));
    });

    document.addEventListener('click', function (e) {
      if (!nav.classList.contains('open')) return;
      if (nav.contains(e.target) || toggle.contains(e.target)) return;
      setNavOpen(false);
    });

    window.addEventListener('resize', function () {
      if (window.innerWidth > 768) setNavOpen(false);
    });
  }

  /* ---------- Demo seed (concurrency page only) ---------- */

  async function loadDemoData(reset) {
    showGlobalLoading(true);
    try {
      const res = await fetch('/api/demo/seed', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ reset: !!reset, include_bookings: true }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error((data && data.error) || 'Seed failed');

      if (data.status === 'already_seeded') {
        showToast('Demo data already loaded', 'info');
        updateDemoUiState(true);
      } else {
        showToast('Demo events & seats loaded!', 'success');
        setTimeout(function () { window.location.reload(); }, 700);
      }
      return data;
    } catch (e) {
      showToast(e.message, 'error');
      throw e;
    } finally {
      showGlobalLoading(false);
    }
  }

  async function checkDemoReady() {
    try {
      const res = await fetch('/api/demo/status');
      const data = await res.json();
      return data.ready === true;
    } catch (e) {
      return false;
    }
  }

  function updateDemoUiState(ready) {
    const btn = $('concurrencyDemoBtn');
    const msg = $('demoDataStatus');
    if (ready) {
      if (btn) hide(btn);
      if (msg) {
        msg.textContent = 'Demo data already loaded';
        show(msg);
      }
    } else {
      if (btn) show(btn);
      if (msg) hide(msg);
    }
  }

  async function initConcurrencyDemoPage() {
    const btn = $('concurrencyDemoBtn');
    const ready = await checkDemoReady();
    updateDemoUiState(ready);
    if (btn && !ready) {
      btn.addEventListener('click', function () { loadDemoData(false); });
    }
  }

  /* ---------- Event cards ---------- */

  function renderEventCard(event, stats) {
    const cat = event.category || 'general';
    const avail = stats ? stats.available_seats : event.total_seats || '—';
    const price = formatINR(event.ticket_price != null ? event.ticket_price : 499);
    const catLabel =
      cat === 'movie' ? 'Movie' : cat === 'concert' ? 'Concert' : cat === 'conference' ? 'Conference' : 'Event';
    const icon =
      cat === 'movie' ? '🎬' : cat === 'concert' ? '🎵' : cat === 'conference' ? '💻' : '🎟️';
    const desc = event.description
      ? escapeHtml(event.description.substring(0, 100)) +
        (event.description.length > 100 ? '...' : '')
      : '';

    return (
      '<article class="event-card event-card-' + escapeHtml(cat) + '">' +
      '<div class="event-card-banner" aria-hidden="true">' +
      '<span class="event-category">' + catLabel + '</span>' +
      '<div class="event-card-banner-icon">' + icon + '</div></div>' +
      '<div class="event-card-body">' +
      '<h3>' + escapeHtml(event.name) + '</h3>' +
      '<p class="event-venue">' + escapeHtml(event.location || 'Venue TBA') + '</p>' +
      '<p class="event-date">' + escapeHtml(formatDate(event.date)) + '</p>' +
      (desc ? '<p class="event-desc">' + desc + '</p>' : '') +
      '<div class="event-card-meta">' +
      '<span class="price-tag">' + price + '</span>' +
      '<span class="seats-tag">' + avail + ' available</span>' +
      '</div></div>' +
      '<div class="event-card-footer">' +
      '<a href="/events/' + event.id + '" class="btn btn-primary btn-block">Book Now</a>' +
      '</div></article>'
    );
  }

  async function loadEventsIntoGrid(grid, loading, errorEl, emptyEl) {
    if (loading) show(loading);
    if (errorEl) hide(errorEl);

    try {
      const res = await apiRequest('GET', '/events');
      if (loading) hide(loading);

      if (!res.ok || !Array.isArray(res.data)) {
        if (errorEl) {
          errorEl.textContent = (res.data && res.data.error) || 'Failed to load events.';
          show(errorEl);
        }
        return;
      }

      if (res.data.length === 0) {
        if (grid) grid.innerHTML = '';
        if (emptyEl) show(emptyEl);
        return;
      }

      if (emptyEl) hide(emptyEl);
      const cards = await Promise.all(
        res.data.map(async function (ev) {
          const st = await apiRequest('GET', '/bookings/event/' + ev.id + '/stats');
          return renderEventCard(ev, st.ok && st.data ? st.data.stats : null);
        })
      );
      if (grid) grid.innerHTML = cards.join('');
      return res.data;
    } catch (e) {
      if (loading) hide(loading);
      if (errorEl) {
        errorEl.textContent = 'Network error: ' + e.message;
        show(errorEl);
      }
    }
  }

  async function refreshHomeStats(events) {
    if (!events || !events.length) return;
    let totalSeats = 0;
    let booked = 0;
    let available = 0;

    await Promise.all(
      events.map(async function (ev) {
        const st = await apiRequest('GET', '/bookings/event/' + ev.id + '/stats');
        if (st.ok && st.data && st.data.stats) {
          totalSeats += st.data.stats.total_seats;
          booked += st.data.stats.booked_seats;
          available += st.data.stats.available_seats;
        }
      })
    );

    const occ = totalSeats > 0 ? ((booked / totalSeats) * 100).toFixed(1) : '0';

    const set = function (id, val) {
      const el = $(id);
      if (el) el.textContent = val;
    };
    set('homeStatEvents', events.length);
    set('homeStatSeats', totalSeats);
    set('homeStatAvailable', available);
    set('homeStatBooked', booked);
    set('homeStatOccupancy', occ + '%');
  }

  function initHomePage() {
    const browseBtn = $('browseEventsBtn');
    if (browseBtn) {
      browseBtn.addEventListener('click', function (e) {
        const target = document.getElementById('featured-events');
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    }

    const grid = $('homeEventsGrid');
    const loading = $('homeEventsLoading');
    const empty = $('homeEventsEmpty');

    if (grid && grid.children.length > 0) {
      apiRequest('GET', '/events').then(function (res) {
        if (res.ok && Array.isArray(res.data)) refreshHomeStats(res.data);
      });
      return;
    }

    show(loading);
    loadEventsIntoGrid(grid, loading, null, empty).then(function (events) {
      if (events) refreshHomeStats(events);
    });
  }

  async function initEventsPage() {
    await loadEventsIntoGrid(
      $('eventsGrid'),
      $('eventsLoading'),
      $('eventsError'),
      $('eventsEmpty')
    );
  }

  /* ---------- Cinema booking ---------- */

  let selectedSeat = null;

  function renderCinemaGrid(container, seats, onSelect) {
    const byRow = {};
    seats.forEach(function (s) {
      const row = s.row_letter || s.seat_number.charAt(0);
      if (!byRow[row]) byRow[row] = [];
      byRow[row].push(s);
    });

    let html = '';
    Object.keys(byRow).sort().forEach(function (rowKey) {
      const rowSeats = byRow[rowKey].sort(function (a, b) {
        return a.seat_number.localeCompare(b.seat_number, undefined, { numeric: true });
      });
      html += '<div class="cinema-row"><span class="row-label">' + escapeHtml(rowKey) + '</span><div class="cinema-row-seats">';
      rowSeats.forEach(function (seat) {
        const booked = seat.status === 'BOOKED';
        const cls = booked ? 'seat-booked' : 'seat-available';
        const label = seat.seat_number.replace(rowKey, '') || seat.seat_number;
        html +=
          '<button type="button" class="seat-btn ' + cls + '" data-id="' + seat.id +
          '" data-num="' + escapeHtml(seat.seat_number) + '"' +
          (booked ? ' disabled title="Already booked"' : ' title="Seat ' + escapeHtml(seat.seat_number) + '"') +
          '>' + escapeHtml(label) + '</button>';
      });
      html += '</div></div>';
    });
    container.innerHTML = html;

    container.querySelectorAll('.seat-btn.seat-available').forEach(function (btn) {
      btn.addEventListener('click', function () {
        container.querySelectorAll('.seat-selected').forEach(function (b) {
          b.classList.remove('seat-selected');
          b.classList.add('seat-available');
        });
        btn.classList.remove('seat-available');
        btn.classList.add('seat-selected');
        selectedSeat = { id: parseInt(btn.dataset.id, 10), seat_number: btn.dataset.num };
        onSelect(selectedSeat);
      });
    });
  }

  function initCinemaBookingPage(event) {
    const grid = $('seatGrid');
    const loading = $('seatsLoading');
    const errorEl = $('seatsError');
    const form = $('inlineBookingForm');
    const bookingError = $('bookingError');

    selectedSeat = null;

    function refreshHeaderStats() {
      apiRequest('GET', '/bookings/event/' + event.id + '/stats').then(function (res) {
        if (res.ok && res.data && res.data.stats) {
          const s = res.data.stats;
          if ($('hdrAvailable')) $('hdrAvailable').textContent = s.available_seats;
          if ($('hdrBooked')) $('hdrBooked').textContent = s.booked_seats;
        }
      });
    }

    function showPanel(seat) {
      hide($('panelHint'));
      show($('panelSummary'));
      show(form);
      $('panelSeat').textContent = seat.seat_number;
      if ($('panelPrice')) $('panelPrice').textContent = formatINR(event.ticket_price || 499);
      $('seatId').value = seat.id;
    }

    apiRequest('GET', '/events/' + event.id + '/seats').then(function (res) {
      hide(loading);
      if (!res.ok || !Array.isArray(res.data)) {
        errorEl.textContent = (res.data && res.data.error) || 'Could not load seats.';
        show(errorEl);
        return;
      }
      if (res.data.length === 0) {
        grid.innerHTML =
          '<p class="empty-state">No seats configured. Load sample data from the How it works page.</p>';
        return;
      }
      renderCinemaGrid(grid, res.data, showPanel);
    });

    form.addEventListener('submit', async function (e) {
      e.preventDefault();
      hide(bookingError);
      const userId = $('userId').value.trim();
      const seatId = parseInt($('seatId').value, 10);
      if (!userId || !seatId) return;

      const btn = $('bookTicketBtn');
      btn.disabled = true;
      showGlobalLoading(true);

      try {
        const res = await apiRequest('POST', '/bookings', { seat_id: seatId, user_id: userId });
        if (res.status === 201 && res.data && res.data.booking) {
          const b = res.data.booking;
          sessionStorage.setItem(
            'lastBooking',
            JSON.stringify({
              booking: b,
              event_name: event.name,
              venue: event.location,
              seat_number: selectedSeat ? selectedSeat.seat_number : $('panelSeat').textContent,
              ticket_price: event.ticket_price,
            })
          );
          showToast('Ticket confirmed!', 'success');
          window.location.href = '/booking/success';
          return;
        }
        if (res.status === 409) {
          bookingError.textContent =
            (res.data && res.data.error) ||
            'Seat already booked — another user won the race (409 Conflict).';
          show(bookingError);
          showToast('Seat unavailable', 'error');
          refreshHeaderStats();
          apiRequest('GET', '/events/' + event.id + '/seats').then(function (r) {
            if (r.ok) renderCinemaGrid(grid, r.data, showPanel);
          });
        } else {
          bookingError.textContent = (res.data && res.data.error) || 'Booking failed.';
          show(bookingError);
        }
      } catch (err) {
        bookingError.textContent = err.message;
        show(bookingError);
      } finally {
        btn.disabled = false;
        showGlobalLoading(false);
      }
    });

    refreshHeaderStats();
  }

  /* ---------- Ticket ---------- */

  function initTicketPage() {
    const wrap = $('ticketWrap');
    const empty = $('ticketEmpty');
    const raw = sessionStorage.getItem('lastBooking');
    if (!raw) {
      hide(wrap);
      show(empty);
      return;
    }
    try {
      const p = JSON.parse(raw);
      const b = p.booking;
      $('ticketEvent').textContent = p.event_name || '—';
      $('ticketVenue').textContent = p.venue || '—';
      $('ticketSeat').textContent = p.seat_number || '—';
      $('ticketBookingId').textContent = b.id;
      $('ticketTransaction').textContent = b.transaction_id || '—';
      $('ticketDate').textContent = formatDate(b.booking_timestamp);
      $('ticketGuest').textContent = b.user_id;
      $('ticketBarcodeText').textContent = 'TF-' + String(b.id).padStart(6, '0');
      const link = $('cancelLink');
      if (link) link.href = '/cancel?booking_id=' + b.id;
      show(wrap);
      hide(empty);

      $('downloadTicketBtn').addEventListener('click', function () {
        const ticket = $('printableTicket');
        const blob = new Blob(
          [
            '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Ticket</title>' +
              '<link rel="stylesheet" href="' + window.location.origin + '/static/css/style.css">' +
              '</head><body style="padding:2rem">' + ticket.outerHTML + '</body></html>',
          ],
          { type: 'text/html' }
        );
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'ticketflow-' + b.id + '.html';
        a.click();
      });
    } catch (e) {
      hide(wrap);
      show(empty);
    }
  }

  /* ---------- Cancel booking (redesigned) ---------- */

  function initCancelPage() {
    const searchBtn = $('searchBookingBtn');
    const confirmBtn = $('confirmCancelBtn');
    const detailsCard = $('cancelDetailsCard');
    const successCard = $('cancelSuccessCard');
    const searchError = $('cancelSearchError');
    const modal = $('cancelConfirmModal');

    cachedBookingLookup = null;

    const pre = getQueryParam('booking_id');
    if (pre) $('bookingId').value = pre;

    function hideAllResults() {
      hide(detailsCard);
      hide(successCard);
      hide(searchError);
    }

    function showBookingDetails(data) {
      cachedBookingLookup = data;
      $('cancelDetailsTitle').textContent = 'Booking #' + data.booking.id;
      $('detailEventName').textContent = data.event_name;
      $('detailSeatNumber').textContent = data.seat_number;
      $('detailVenue').textContent = data.event_location || '—';
      $('detailTransaction').textContent = data.transaction_display;
      $('detailGuest').textContent = data.booking.user_id;
      $('detailBookedAt').textContent = formatDate(data.booking.booking_timestamp);

      const badge = $('cancelStatusBadge');
      if (data.seat_status === 'BOOKED') {
        badge.textContent = 'Active';
        badge.className = 'badge badge-active';
        confirmBtn.disabled = false;
      } else {
        badge.textContent = 'Already released';
        badge.className = 'badge badge-released';
        confirmBtn.disabled = true;
      }

      show(detailsCard);
      hide(successCard);
    }

    async function searchBooking() {
      hideAllResults();
      cachedBookingLookup = null;
      confirmBtn.disabled = true;

      const id = $('bookingId').value.trim();
      if (!id) {
        searchError.textContent = 'Please enter a Booking ID.';
        show(searchError);
        return;
      }

      searchBtn.disabled = true;
      const res = await fetchUiBooking(id);
      searchBtn.disabled = false;

      if (!res.ok || !res.data) {
        searchError.textContent = (res.data && res.data.error) || 'Booking not found.';
        show(searchError);
        return;
      }

      showBookingDetails(res.data);
    }

    searchBtn.addEventListener('click', searchBooking);

    $('bookingId').addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        searchBooking();
      }
    });

    if (pre) searchBooking();

    confirmBtn.addEventListener('click', function () {
      if (!cachedBookingLookup) {
        searchError.textContent = 'Search for a booking before cancelling.';
        show(searchError);
        return;
      }
      $('modalMessage').textContent =
        'Are you sure you want to cancel booking #' +
        cachedBookingLookup.booking.id +
        ' for seat ' +
        cachedBookingLookup.seat_number +
        '?';
      show(modal);
    });

    $('modalCancelBtn').addEventListener('click', function () { hide(modal); });
    $('modalBackdrop').addEventListener('click', function () { hide(modal); });

    $('modalConfirmBtn').addEventListener('click', async function () {
      hide(modal);
      if (!cachedBookingLookup) return;

      const id = cachedBookingLookup.booking.id;
      const seatNum = cachedBookingLookup.seat_number;
      confirmBtn.disabled = true;
      showGlobalLoading(true);

      const res = await apiRequest('DELETE', '/bookings/' + id);
      showGlobalLoading(false);

      if (res.ok) {
        hide(detailsCard);
        show(successCard);
        $('cancelSuccessMessage').textContent =
          'Booking #' + id + ' was cancelled successfully. Seat ' + seatNum + ' is now available again.';
        sessionStorage.removeItem('lastBooking');
        showToast('Booking cancelled', 'success');
        cachedBookingLookup = null;
      } else {
        searchError.textContent = (res.data && res.data.error) || 'Cancellation failed.';
        show(searchError);
        confirmBtn.disabled = false;
      }
    });
  }

  /* ---------- Statistics ---------- */

  function updateCharts(stats) {
    const total = stats.total_seats || 1;
    const booked = stats.booked_seats || 0;
    const available = stats.available_seats || 0;
    const pctBooked = (booked / total) * 100;
    const pctAvail = (available / total) * 100;

    $('chartAvailable').style.width = pctAvail + '%';
    $('chartBooked').style.width = pctBooked + '%';
    $('chartAvailableVal').textContent = available;
    $('chartBookedVal').textContent = booked;
    $('occupancyBar').style.width = stats.occupancy_rate + '%';
  }

  async function loadOverviewStats() {
    const res = await apiRequest('GET', '/events');
    if (!res.ok || !Array.isArray(res.data) || res.data.length === 0) return;

    let total = 0;
    let booked = 0;
    let available = 0;

    await Promise.all(
      res.data.map(async function (ev) {
        const st = await apiRequest('GET', '/bookings/event/' + ev.id + '/stats');
        if (st.ok && st.data && st.data.stats) {
          total += st.data.stats.total_seats;
          booked += st.data.stats.booked_seats;
          available += st.data.stats.available_seats;
        }
      })
    );

    const occ = total > 0 ? (booked / total) * 100 : 0;
    $('overviewEvents').textContent = res.data.length;
    $('overviewTotal').textContent = total;
    $('overviewAvailable').textContent = available;
    $('overviewBooked').textContent = booked;
    $('overviewOccupancy').textContent = occ.toFixed(1) + '%';
    show($('statsOverview'));
  }

  async function initStatsPage(initialId) {
    const select = $('eventSelect');
    const loading = $('statsLoading');
    const errorEl = $('statsError');
    const content = $('statsContent');
    const statsEmpty = $('statsEmpty');

    loadOverviewStats();

    async function loadEventStats(id) {
      if (!id) {
        hide(content);
        return;
      }
      show(loading);
      hide(errorEl);
      const res = await apiRequest('GET', '/bookings/event/' + id + '/stats');
      hide(loading);

      if (!res.ok || !res.data || !res.data.stats) {
        errorEl.textContent = 'Failed to load statistics';
        show(errorEl);
        return;
      }

      hide(statsEmpty);
      const s = res.data.stats;
      $('statTotal').textContent = s.total_seats;
      $('statAvailable').textContent = s.available_seats;
      $('statBooked').textContent = s.booked_seats;
      $('statOccupancy').textContent = s.occupancy_rate.toFixed(1) + '%';
      const name = select.options[select.selectedIndex].text;
      $('occupancyCaption').textContent =
        s.booked_seats + ' of ' + s.total_seats + ' seats booked for ' + name;
      updateCharts(s);
      show(content);
    }

    select.addEventListener('change', function () {
      const id = select.value;
      if (id) history.replaceState(null, '', '/stats/' + id);
      else {
        history.replaceState(null, '', '/stats');
        hide(content);
      }
      loadEventStats(id);
    });

    if (initialId) loadEventStats(String(initialId));
    else if (select.value) loadEventStats(select.value);
  }

  document.addEventListener('DOMContentLoaded', function () {
    initNavToggle();
    checkHealth();
  });

  return {
    formatINR: formatINR,
    loadDemoData: loadDemoData,
    initHomePage: initHomePage,
    initEventsPage: initEventsPage,
    initCinemaBookingPage: initCinemaBookingPage,
    initTicketPage: initTicketPage,
    initBookingSuccessPage: initTicketPage,
    initCancelPage: initCancelPage,
    initStatsPage: initStatsPage,
    initConcurrencyDemoPage: initConcurrencyDemoPage,
  };
})();
