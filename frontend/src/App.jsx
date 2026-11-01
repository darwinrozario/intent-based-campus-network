import { useEffect, useState } from "react";
import {
  getDepartments,
  getPolicies,
  applyIntent,
  updatePolicy,
  getNetworkMetrics,
  getActivities
} from "./services/api";

function App() {
  const [departments, setDepartments] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [network, setNetwork] = useState(null);
  const [activities, setActivities] = useState([]);
  const [intent, setIntent] = useState("");
  const [loading, setLoading] = useState(false);
  const [updatingPolicy, setUpdatingPolicy] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const formatName = (value = "") =>
    value
      .split("-")
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");

  const fetchDepartments = async () => {
    try {
      const data = await getDepartments();
      setDepartments(data.departments || []);
    } catch (err) {
      setError("Unable to fetch campus departments.");
    }
  };

  const fetchPolicies = async () => {
    try {
      const data = await getPolicies();
      setPolicies(data.policies || []);
    } catch (err) {
      setError("Unable to fetch network policies.");
    }
  };

  const fetchNetworkMetrics = async () => {
    try {
      const data = await getNetworkMetrics();
      setNetwork(data);
    } catch (err) {
      setNetwork(null);
      setError("Unable to retrieve network monitoring information.");
    }
  };

  const fetchActivities = async () => {
    try {
      const data = await getActivities();
      setActivities(data.activities || []);
    } catch (err) {
      setError("Unable to retrieve activity logs.");
    }
  };

  const refreshDashboard = () => {
    fetchDepartments();
    fetchPolicies();
    fetchNetworkMetrics();
    fetchActivities();
  };

  useEffect(() => {
    refreshDashboard();

    const interval = setInterval(refreshDashboard, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleApplyIntent = async (e) => {
    e.preventDefault();

    if (!intent.trim()) return;

    setLoading(true);
    setMessage("");
    setError("");

    try {
      const result = await applyIntent(intent);

      const action =
        result.interpreted_intent?.action ||
        result.action ||
        "updated";

      setMessage(
        `Intent applied successfully! Action: ${String(action).toUpperCase()}. ` +
        `Active blocking rules: ${result.active_blocking_rules ?? "--"}.`
      );

      setIntent("");
      refreshDashboard();

    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to apply intent."
      );
    } finally {
      setLoading(false);
    }
  };

  const handlePolicyUpdate = async (policyName, action) => {
    setUpdatingPolicy(policyName);
    setMessage("");
    setError("");

    try {
      const result = await updatePolicy(policyName, action);

      setMessage(
        `Policy ${policyName} updated to ${String(result.action || action).toUpperCase()}. ` +
        `Active blocking rules: ${result.active_blocking_rules ?? "--"}.`
      );

      refreshDashboard();

    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to update policy."
      );
    } finally {
      setUpdatingPolicy(null);
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return "-";

    const date = new Date(timestamp);

    return Number.isNaN(date.getTime())
      ? timestamp
      : date.toLocaleString();
  };

  const getPortStatus = (portNumber) => {
    const port = network?.ports?.find(
      (item) => Number(item.port) === Number(portNumber)
    );

    return {
      port,
      isUp: network?.status === "OPERATIONAL" && port?.status === "UP"
    };
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">

      {/* Header */}
      <header className="mb-10">
        <h1 className="text-3xl font-bold text-cyan-400">
          Campus Network Management
        </h1>

        <p className="text-slate-400 mt-2">
          Intent-Based Network Administration Dashboard
        </p>

        <p className="text-xs text-slate-500 mt-2">
          Live monitoring refreshes every 5 seconds
        </p>
      </header>

      {/* Dashboard Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        <div className="bg-slate-900 p-6 rounded-xl border border-slate-800">
          <p className="text-slate-400">Switch Status</p>

          <h2 className={`text-2xl font-semibold mt-3 ${
            network?.status === "OPERATIONAL"
              ? "text-green-400"
              : "text-amber-400"
          }`}>
            {network?.status || "Checking..."}
          </h2>
        </div>

        <div className="bg-slate-900 p-6 rounded-xl border border-slate-800">
          <p className="text-slate-400">Connected Ports</p>

          <h2 className="text-2xl font-semibold mt-3">
            {network?.ports?.filter(
              (port) => port.status === "UP"
            ).length ?? "--"}
          </h2>
        </div>

        <div className="bg-slate-900 p-6 rounded-xl border border-slate-800">
          <p className="text-slate-400">Active Blocking Rules</p>

          <h2 className="text-2xl font-semibold text-red-400 mt-3">
            {network?.flow_statistics?.active_blocking_rules ?? "--"}
          </h2>
        </div>

      </div>

      {/* Network Traffic Statistics */}
      <section className="mt-8 bg-slate-900 border border-slate-800 rounded-xl p-6">

        <h2 className="text-xl font-semibold mb-5">
          Network Traffic Statistics
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

          <div className="bg-slate-800 p-5 rounded-lg">
            <p className="text-slate-400">Total Packets</p>

            <h3 className="text-3xl font-bold text-cyan-400 mt-2">
              {network?.flow_statistics?.total_packets ?? "--"}
            </h3>
          </div>

          <div className="bg-slate-800 p-5 rounded-lg">
            <p className="text-slate-400">Total Bytes</p>

            <h3 className="text-3xl font-bold text-cyan-400 mt-2">
              {network?.flow_statistics?.total_bytes ?? "--"}
            </h3>
          </div>

        </div>
      </section>

      {/* Dynamic Network Topology */}
      <section className="mt-10 bg-slate-900 border border-slate-800 rounded-xl p-6">

        <div className="flex flex-wrap justify-between items-center gap-3 mb-8">

          <div>
            <h2 className="text-xl font-semibold">
              Network Topology
            </h2>

            <p className="text-sm text-slate-400 mt-1">
              Six campus departments retrieved dynamically through NETCONF
            </p>
          </div>

          <span className={`text-sm ${
            network?.status === "OPERATIONAL"
              ? "text-green-400"
              : "text-amber-400"
          }`}>
            {network?.status || "Checking..."}
          </span>

        </div>

        <div className="flex flex-col items-center">

          {/* Open vSwitch */}
          <div className="bg-indigo-600 border border-indigo-400 rounded-xl px-10 py-5 text-center shadow-lg">

            <h3 className="text-lg font-bold">
              Open vSwitch
            </h3>

            <p className="text-sm text-indigo-200 mt-1">
              Switch s1
            </p>

            <p className="text-xs text-indigo-200 mt-2">
              Software Defined Network
            </p>

          </div>

          <div className="w-1 h-10 bg-slate-600"></div>

          {/* Department Cards */}
          {departments.length === 0 ? (

            <p className="text-slate-400 py-6">
              Loading department topology...
            </p>

          ) : (

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 w-full">

              {departments.map((department) => {

                const memberStatuses = (
                  department.members || []
                ).map((member) => ({
                  member,
                  ...getPortStatus(member.switch_port)
                }));

                const connectedCount = memberStatuses.filter(
                  (item) => item.isUp
                ).length;

                const allConnected =
                  memberStatuses.length > 0 &&
                  connectedCount === memberStatuses.length;

                return (

                  <article
                    key={department.name}
                    className={`rounded-xl border p-5 ${
                      allConnected
                        ? "bg-slate-800 border-slate-700"
                        : "bg-slate-800 border-amber-800"
                    }`}
                  >

                    <div className="flex justify-between items-start gap-2">

                      <h3 className="font-semibold">
                        {formatName(department.name)}
                      </h3>

                      <span className="text-xs rounded-full bg-indigo-950 text-indigo-300 px-2 py-1">
                        VLAN {department.vlan_id}
                      </span>

                    </div>

                    <p className="text-cyan-400 text-sm mt-3">
                      {department.subnet}
                    </p>

                    <p className="text-xs text-slate-400 mt-2">
                      {connectedCount}/{memberStatuses.length} devices connected
                    </p>

                    <div className="mt-4 space-y-3">

                      {memberStatuses.map(({ member, port, isUp }) => (

                        <div
                          key={member.name}
                          className="flex justify-between items-center gap-3 border-t border-slate-700 pt-3"
                        >

                          <div>
                            <p className="text-sm font-medium">
                              {member.name}
                            </p>

                            <p className="text-xs text-slate-400">
                              {member.ip_address}
                            </p>
                          </div>

                          <div className="text-right">

                            <p className="text-xs text-slate-400">
                              Port {member.switch_port}
                            </p>

                            <p className={`text-xs font-semibold ${
                              isUp
                                ? "text-green-400"
                                : "text-amber-400"
                            }`}>
                              {port ? port.status : "UNKNOWN"}
                            </p>

                          </div>

                        </div>

                      ))}

                    </div>

                  </article>

                );

              })}

            </div>

          )}

        </div>

        {/* Logical Network Policies */}
        <div className="mt-8 border-t border-slate-700 pt-6">

          <h3 className="font-semibold mb-4">
            Logical Network Policies
          </h3>

          {policies.length === 0 ? (

            <p className="text-sm text-slate-400">
              No configured policies.
            </p>

          ) : (

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

              {policies.map((policy) => {

                const blocked =
                  policy.enabled && policy.action === "block";

                return (

                  <div
                    key={policy.name}
                    className="bg-slate-800 rounded-lg p-4 border border-slate-700"
                  >

                    <p className="font-medium">
                      {policy.name}
                    </p>

                    <div className="flex flex-wrap items-center gap-2 mt-3 text-sm">

                      <span>
                        {formatName(policy.source)}
                      </span>

                      <span className="text-slate-500">
                        →
                      </span>

                      <span>
                        {formatName(policy.destination)}
                      </span>

                    </div>

                    <p className={`text-xs font-semibold mt-3 ${
                      blocked
                        ? "text-red-400"
                        : "text-green-400"
                    }`}>
                      {policy.enabled
                        ? blocked
                          ? "BLOCK POLICY ENABLED"
                          : "ALLOW POLICY ENABLED"
                        : "POLICY DISABLED"}
                    </p>

                  </div>

                );

              })}

            </div>

          )}

          <div className="flex flex-wrap gap-5 mt-6 text-sm">

            <span className="text-green-400">
              ● Allowed
            </span>

            <span className="text-red-400">
              ● Blocked
            </span>

            <span className="text-slate-400">
              ● Unavailable
            </span>

          </div>

        </div>

      </section>

      {/* Intent Management */}
      <section className="mt-10 bg-slate-900 border border-slate-800 rounded-xl p-6">

        <h2 className="text-xl font-semibold mb-5">
          Intent Management
        </h2>

        <form
          onSubmit={handleApplyIntent}
          className="flex flex-col gap-4"
        >

          <textarea
            value={intent}
            onChange={(e) => setIntent(e.target.value)}
            placeholder="Example: Block communication from Computer Science to Administration"
            className="w-full bg-slate-800 border border-slate-700 rounded-lg p-4 outline-none focus:border-cyan-400"
            rows="3"
          />

          <button
            type="submit"
            disabled={loading || !intent.trim()}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 px-6 py-3 rounded-lg font-semibold"
          >
            {loading ? "Applying Intent..." : "Apply Intent"}
          </button>

        </form>

      </section>

      {/* Notifications */}
      {(message || error) && (

        <div className={`mt-6 p-4 rounded-lg border ${
          error
            ? "bg-red-950 border-red-800 text-red-300"
            : "bg-green-950 border-green-800 text-green-300"
        }`}>
          {error || message}
        </div>

      )}

      {/* Network Policies */}
      <section className="mt-10 bg-slate-900 border border-slate-800 rounded-xl p-6">

        <div className="flex justify-between items-center mb-5">

          <h2 className="text-xl font-semibold">
            Network Policies
          </h2>

          <button
            onClick={refreshDashboard}
            className="text-cyan-400 hover:text-cyan-300 text-sm"
          >
            Refresh
          </button>

        </div>

        {policies.length === 0 ? (

          <p className="text-slate-400">
            No policies found.
          </p>

        ) : (

          <div className="overflow-x-auto">

            <table className="w-full text-left">

              <thead>
                <tr className="text-slate-400 border-b border-slate-700">
                  <th className="p-3">Policy Name</th>
                  <th className="p-3">Source</th>
                  <th className="p-3">Destination</th>
                  <th className="p-3">Action</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Controls</th>
                </tr>
              </thead>

              <tbody>

                {policies.map((policy) => (

                  <tr
                    key={policy.name}
                    className="border-b border-slate-800"
                  >

                    <td className="p-3">
                      {policy.name}
                    </td>

                    <td className="p-3">
                      {formatName(policy.source)}
                    </td>

                    <td className="p-3">
                      {formatName(policy.destination)}
                    </td>

                    <td className="p-3">

                      <span className={
                        policy.action === "block"
                          ? "text-red-400"
                          : "text-green-400"
                      }>
                        {(policy.action || "").toUpperCase()}
                      </span>

                    </td>

                    <td className="p-3">

                      {policy.enabled ? (

                        <span className="text-green-400">
                          Enabled
                        </span>

                      ) : (

                        <span className="text-slate-500">
                          Disabled
                        </span>

                      )}

                    </td>

                    <td className="p-3">

                      <div className="flex gap-2">

                        <button
                          onClick={() => handlePolicyUpdate(policy.name, "allow")}
                          disabled={
                            updatingPolicy === policy.name ||
                            policy.action === "allow"
                          }
                          className="bg-green-700 hover:bg-green-600 disabled:opacity-30 px-3 py-2 rounded text-sm"
                        >
                          Allow
                        </button>

                        <button
                          onClick={() => handlePolicyUpdate(policy.name, "block")}
                          disabled={
                            updatingPolicy === policy.name ||
                            policy.action === "block"
                          }
                          className="bg-red-700 hover:bg-red-600 disabled:opacity-30 px-3 py-2 rounded text-sm"
                        >
                          Block
                        </button>

                      </div>

                      {updatingPolicy === policy.name && (

                        <p className="text-xs text-cyan-400 mt-2">
                          Updating...
                        </p>

                      )}

                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        )}

      </section>

      {/* Activity Logs */}
      <section className="mt-10 bg-slate-900 border border-slate-800 rounded-xl p-6">

        <div className="flex justify-between items-center mb-5">

          <div>
            <h2 className="text-xl font-semibold">
              Network Activity Logs
            </h2>

            <p className="text-sm text-slate-400 mt-1">
              Recent policy changes and intent executions
            </p>
          </div>

          <button
            onClick={fetchActivities}
            className="text-cyan-400 hover:text-cyan-300 text-sm"
          >
            Refresh Logs
          </button>

        </div>

        {activities.length === 0 ? (

          <p className="text-slate-400">
            No activity records available.
          </p>

        ) : (

          <div className="overflow-x-auto">

            <table className="w-full text-left">

              <thead>
                <tr className="text-slate-400 border-b border-slate-700">
                  <th className="p-3">Time</th>
                  <th className="p-3">Event</th>
                  <th className="p-3">Source</th>
                  <th className="p-3">Destination</th>
                  <th className="p-3">Action</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Description</th>
                </tr>
              </thead>

              <tbody>

                {activities.map((activity) => (

                  <tr
                    key={activity.id}
                    className="border-b border-slate-800"
                  >

                    <td className="p-3 text-sm whitespace-nowrap">
                      {formatTimestamp(activity.timestamp)}
                    </td>

                    <td className="p-3 text-sm">
                      {activity.event_type}
                    </td>

                    <td className="p-3">
                      {formatName(activity.source || "-")}
                    </td>

                    <td className="p-3">
                      {formatName(activity.destination || "-")}
                    </td>

                    <td className="p-3">

                      <span className={
                        String(activity.action).toUpperCase() === "BLOCK"
                          ? "text-red-400"
                          : "text-green-400"
                      }>
                        {activity.action || "-"}
                      </span>

                    </td>

                    <td className="p-3">

                      <span className={
                        String(activity.status).toUpperCase() === "APPLIED" ||
                        String(activity.status).toUpperCase() === "SUCCESS"
                          ? "text-green-400"
                          : "text-amber-400"
                      }>
                        {activity.status || "-"}
                      </span>

                    </td>

                    <td className="p-3 text-sm text-slate-400">
                      {activity.description || "-"}
                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        )}

      </section>

    </div>
  );
}

export default App;
