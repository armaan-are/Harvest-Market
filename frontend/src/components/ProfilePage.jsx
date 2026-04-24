import { useState } from "react";
import DashboardSidebar from "./DashboardSidebar";

export default function ProfilePage({ currentUser, profile, onSaveProfile, loading }) {
  const [form, setForm] = useState(profile || {});

  if (!currentUser) {
    return (
      <div className="empty-state">
        <h3>Sign in to manage your profile.</h3>
      </div>
    );
  }

  const isBuyer = currentUser.role === "buyer";

  return (
    <div className="dashboard-shell">
      <DashboardSidebar currentUser={currentUser} activeSection="profile" />

      <section className="seller-panel profile-panel">
        <div className="section-heading">
          <p className="eyebrow">{isBuyer ? "Neighbor Profile" : "Farm Profile"}</p>
          <h1>
            {isBuyer
              ? "Store local contact information and your home zip code."
              : "Control the public farm page buyers see when they order from you."}
          </h1>
        </div>

        <form
          className="seller-form profile-form"
          onSubmit={(event) => {
            event.preventDefault();
            onSaveProfile(form);
          }}
        >
          <label>
            Email
            <input type="email" value={currentUser.email} disabled />
          </label>

          {isBuyer ? (
            <>
              <label>
                Full name
                <input
                  type="text"
                  value={form.full_name || ""}
                  onChange={(event) => setForm({ ...form, full_name: event.target.value })}
                />
              </label>
              <label>
                Phone
                <input
                  type="text"
                  value={form.phone || ""}
                  onChange={(event) => setForm({ ...form, phone: event.target.value })}
                />
              </label>
              <label>
                Home zip
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]{5}"
                  maxLength="5"
                  value={form.home_zip || ""}
                  onChange={(event) => setForm({ ...form, home_zip: event.target.value })}
                />
              </label>
            </>
          ) : (
            <>
              <label>
                Farm name
                <input
                  type="text"
                  value={form.farm_name || ""}
                  onChange={(event) => setForm({ ...form, farm_name: event.target.value })}
                />
              </label>
              <label>
                Biography
                <textarea
                  rows="4"
                  value={form.biography || ""}
                  onChange={(event) => setForm({ ...form, biography: event.target.value })}
                />
              </label>
              <label>
                Pickup address
                <input
                  type="text"
                  value={form.pickup_address || ""}
                  onChange={(event) => setForm({ ...form, pickup_address: event.target.value })}
                />
              </label>
              <label>
                Operating hours
                <input
                  type="text"
                  value={form.operating_hours || ""}
                  onChange={(event) => setForm({ ...form, operating_hours: event.target.value })}
                />
              </label>
              <label>
                Zip code
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]{5}"
                  maxLength="5"
                  value={form.zip_code || ""}
                  onChange={(event) => setForm({ ...form, zip_code: event.target.value })}
                />
              </label>
            </>
          )}

          <button className="button button--primary" type="submit" disabled={loading}>
            {loading ? "Saving..." : "Save Profile"}
          </button>
        </form>
      </section>
    </div>
  );
}
