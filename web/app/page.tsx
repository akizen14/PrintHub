import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="max-w-2xl w-full text-center space-y-8">
        <div className="space-y-4">
          <h1 className="text-5xl font-bold text-gray-900">PrintHub</h1>
          <p className="text-xl text-gray-600">
            Fast, easy print ordering for students
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/order/new"
            className="px-8 py-4 bg-teal-600 text-white rounded-lg font-semibold text-lg hover:bg-teal-700 transition-colors"
          >
            New Order
          </Link>
          <Link
            href="/orders"
            className="px-8 py-4 bg-white border-2 border-teal-600 text-teal-600 rounded-lg font-semibold text-lg hover:bg-teal-50 transition-colors"
          >
            My Orders
          </Link>
        </div>

        <div className="pt-8 text-sm text-gray-500">
          <p>Track your print jobs in real-time</p>
        </div>
      </div>
    </div>
  );
}
